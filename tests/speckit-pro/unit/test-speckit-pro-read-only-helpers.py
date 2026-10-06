#!/usr/bin/env python3
"""Stdlib-only tests for read-only runner helpers."""

from __future__ import annotations

import argparse
import copy
import functools
import hashlib
import itertools
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Iterator
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
GENERIC_CAPTURE_LIMIT_BYTES = 16 * 1024
PLAN_LAYERS_CAPTURE_LIMIT_BYTES = 256 * 1024
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "read-only-helpers"
PLAN_LAYERS_FIXTURE_DIR = "tests/speckit-pro/unit/fixtures/plan-layers"
FEATURE_DIR = "tests/speckit-pro/unit/fixtures/read-only-helpers/read-only-helper-feature"
ARCHIVED_FEATURE_DIR = "specs/spec-900-archived-feature"
REPOSITORY_BASH_CONFINEMENT_PLAN_DIR = (
    "tests/speckit-pro/unit/fixtures/plan-layers/repository-bash-confinement-plan"
)
WORKFLOW_FILE = "tests/speckit-pro/unit/fixtures/autopilot-stage/workflow.md"
AUTOPILOT_STAGE_WORKFLOW_FILE = WORKFLOW_FILE
PR_PACKET_FIXTURE_DIR = REPO_ROOT / "tests" / "speckit-pro" / "unit" / "fixtures" / "pr-packet"
DRAFT_PACKET_VALIDATION_DIR = "specs/fixture-draft-pr/.process/pr-packets"
PR_PACKET_SCHEMA = (
    PLUGIN_ROOT / "skills" / "speckit-autopilot" / "contracts" / "pr-packet.schema.json"
)
# Shipped runbooks that tell an operator what to do with the confidence-gate
# JSON on the exit-2 path. All three describe the same loop, so they have to
# agree on which field the loop reads first.
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tests" / "speckit-pro" / "lib"))
from script_loader import load_script  # noqa: E402
from host_skill_views import host_skill_root  # noqa: E402

CONFIDENCE_GATE_RUNBOOKS = (
    PLUGIN_ROOT / "skills" / "speckit-autopilot" / "references" / "gate-validation.md",
    *(host_skill_root(host) / "speckit-autopilot" / "references" / "phase-execution.md" for host in ("claude", "codex")),
)
import runner_invocation  # noqa: E402
from runner_invocation import assert_runner_response, command_stdin_fixture  # noqa: E402

from speckit_pro_runner.helpers import registry  # noqa: E402
from speckit_pro_runner.pr_contract import PACKET_TITLE_SCOPE_PATTERN, PACKET_TITLE_VALUE_PATTERN  # noqa: E402

EXPECTED_HELPERS = [
    "select-artifact-pages",
    "g0-setup",
    "formal-doctor",
    "probe-git-write",
    "scaffold-answers",
    "phase-brief",
    "helper-registry-dispatch",
    "check-prerequisites",
    "resolve-workflow-binding",
    "resolve-scaffold-worktree-placement",
    "render-plan-repair-context",
    "detect-commands",
    "detect-presets",
    "count-markers",
    "validate-gate",
    "reviewability-gate",
    "estimate-reviewable-loc",
    "resolve-confidence-mode",
    "resolve-autopilot-stage",
    "resolve-claude-subagent-runtime",
    "validate-agent-install",
    "confidence-gate",
    "generate-spec-index-check",
    "o5-topology",
    "atomicity-route",
    "plan-layers-feature-dir",
    "validate-pr-workflow-contract",
    "validate-pr-packet-read-only",
    "estimate-spec-size",
    "sweep-pr-feedback",
    "sweep-isolation-session",
    "preview-isolation-session",
    "check-artifact-freshness",
    "partition-phase7-tasks",
    "validate-task-execution",
    "validate-execution-record",
    "parse-consensus-categories",
    "aggregate-crl",
    "research-broker-preflight",
    "render-egress-authorization",
    "check-gate-preflight-coverage",
    "finalize-run",
    "ratify-pr-split",
    "list-archive-candidates",
    "check-roadmap-freshness",
]

JSON_STDOUT_PARITY_HELPERS = {"atomicity-route"}

HELPER_CASES: dict[str, dict[str, object]] = {
    "g0-setup": {"probe": "commands", "surface": "codex", "workflow_file": WORKFLOW_FILE},
    "probe-git-write": {},
    "scaffold-answers": {"answers_file": "missing-answers.json", "spec_id": "SPEC-009"},
    "formal-doctor": {"repo_root": ".", "workflow_file": "tests/speckit-pro/unit/fixtures/formal-methods/disabled-workflow.md"},
    "check-prerequisites": {"workflow_file": WORKFLOW_FILE},
    "resolve-workflow-binding": {"workflow_file": AUTOPILOT_STAGE_WORKFLOW_FILE},
    "resolve-scaffold-worktree-placement": {"branch_name": "test-scaffold-placement"},
    "render-plan-repair-context": {
        "context_paths": {
            "original-plan-prompt": "tests/speckit-pro/unit/fixtures/read-only-helpers/plan-repair-original.md",
            "source-evidence": "tests/speckit-pro/unit/fixtures/read-only-helpers/plan-repair-source.md",
        },
        "g3_attempts_path": "tests/speckit-pro/unit/fixtures/read-only-helpers/plan-repair-attempts.json",
        "g3_attempt_index": 0,
        "executor_task": "Remove only the unsupported exact-render strengthening.",
        "attempt_number": 1,
        "disputed_wording": "exact client render timing",
        "provenance_class": "assistant-inference",
        "prior_repair_result": "initial G3 failure",
    },
    "detect-commands": {},
    "detect-presets": {},
    "count-markers": {"type": "all", "feature_dir": FEATURE_DIR},
    "validate-gate": {"gate": "G7", "feature_dir": FEATURE_DIR},
    "reviewability-gate": {"mode_name": "setup", "target": WORKFLOW_FILE},
    "estimate-reviewable-loc": {"plan_file": f"{FEATURE_DIR}/plan.md"},
    "resolve-confidence-mode": {"autopilot_args": ["--advisory", WORKFLOW_FILE]},
    "resolve-autopilot-stage": {
        "workflow_file": AUTOPILOT_STAGE_WORKFLOW_FILE,
        "autopilot_args": ["--stage", "plan"],
    },
    "resolve-claude-subagent-runtime": {
        "client_version": "2.1.251 (Claude Code)",
        "execution_mode": "interactive",
        "agent_teams_env_enabled": True,
        "team_contract_verified": True,
        "auto_memory_enabled": True,
    },
    "validate-agent-install": {"surface": "claude"},
    "confidence-gate": {"workflow_file": WORKFLOW_FILE, "mode_name": "advisory"},
    "generate-spec-index-check": {},
    "o5-topology": {"target": FEATURE_DIR},
    "atomicity-route": {"feature_dir": FEATURE_DIR, "workflow_file": WORKFLOW_FILE},
    "plan-layers-feature-dir": {"feature_dir": FEATURE_DIR},
    "partition-phase7-tasks": {"tasks_file": f"{FEATURE_DIR}/tasks.md", "wave_size": 4},
    "validate-task-execution": {"tasks_file": f"{FEATURE_DIR}/tasks.md", "action": "fingerprints"},
    "validate-execution-record": {"workflow_file": WORKFLOW_FILE, "command_id": "UNIT_TEST",
                                  "record_path": "tests/speckit-pro/unit/fixtures/autopilot-stage/.process/verification/missing.json"},
    "parse-consensus-categories": {"line": "[codebase, domain] Q1: bcrypt or argon2?"},
    "aggregate-crl": {"workflow_file": AUTOPILOT_STAGE_WORKFLOW_FILE},
    "validate-pr-workflow-contract": {"title": "feat(FEATURE-001): Validate helper contract"},
    "validate-pr-packet-read-only": {"packet_path": "tests/speckit-pro/unit/fixtures/read-only-helpers/missing-pr-packet.json"},
    "estimate-spec-size": {"user_stories": 2, "files": 3, "frs": 4},
    "select-artifact-pages": {"plan_file": FEATURE_DIR + "/plan.md"},
    "research-broker-preflight": {},
    "render-egress-authorization": json.loads(
        (REPO_ROOT / "tests/speckit-pro/unit/fixtures/read-only-helpers/requests/render-egress-authorization.json")
        .read_text(encoding="utf-8")
    )["inputs"],
    "check-gate-preflight-coverage": json.loads(
        (REPO_ROOT / "tests/speckit-pro/unit/fixtures/read-only-helpers/requests/check-gate-preflight-coverage.json")
        .read_text(encoding="utf-8")
    )["inputs"],
    "finalize-run": json.loads(
        (REPO_ROOT / "tests/speckit-pro/unit/fixtures/read-only-helpers/requests/finalize-run.json")
        .read_text(encoding="utf-8")
    )["inputs"],
    "ratify-pr-split": json.loads(
        (REPO_ROOT / "tests/speckit-pro/unit/fixtures/read-only-helpers/requests/ratify-pr-split.json")
        .read_text(encoding="utf-8")
    )["inputs"],
    "list-archive-candidates": {"current_target": "specs/001-current-feature"},
    "check-roadmap-freshness": {"roadmap_path": "docs/ai/technical-roadmap.md"},
    "sweep-pr-feedback": {
        "workflow_file": "docs/ai/specs/.process/FEATURE-002-workflow.md",
        "self_login": "speckit-pro-bot",
        "feature_dir": "specs/fixture-feedback-sweep",
        "pr_observation": {
            "ok": True,
            "comments": [
                {
                    "id": "IC_kwDO...",
                    "surface": "pr_conversation",
                    "author": "octocat",
                    "author_association": "OWNER",
                    "body": (
                        "Artifact: Implementation Plan\nFeature: FEATURE-002\n\n"
                        "Objections recorded while reviewing this plan.\n\n"
                        "Phase / Registry  (#phase-2)\n"
                        "The registry should cover every exporting template."
                    ),
                    "truncated": False,
                },
                {
                    "id": "PRRC_kwDO...",
                    "surface": "review_thread",
                    "author": None,
                    "author_association": "CONTRIBUTOR",
                    "body": "Drive-by suggestion.",
                    "truncated": False,
                    "thread_resolved": False,
                },
            ],
        },
    },
    "sweep-isolation-session": {"named_surface": "attest_claude"},
    "preview-isolation-session": {"named_surface": "attest_codex"},
    "check-artifact-freshness": {
        "workflow_file": "docs/ai/specs/.process/FEATURE-002-workflow.md",
        "artifacts_observation": {
            "ok": True,
            "artifacts_dir_state": "present",
            "last_artifacts_commit": "9f2c1ab8d4e5f60718293a4b5c6d7e8f90123456",
            "pages": ["implementation-plan", "spec-explainer"],
            "amended_commits": [
                {
                    "cell": "a1b2c3d",
                    "resolved": True,
                    "is_ancestor_of_artifacts_commit": True,
                },
            ],
        },
    },
}


def roadmap_budget_entry(spec_id: str, name: str, surface: str, loc: int, prod: int, total: int) -> str:
    return (
        f"### {spec_id}: {name}\n\n"
        "**Priority:** P1 | **Depends On:** None | **Enables:** None\n\n"
        f"**Reviewability Budget:** Primary surface: {surface} |\n"
        f"Projected reviewable LOC: {loc} |\n"
        f"Production files: {prod} |\n"
        f"Total files: {total} |\n"
        "Budget result: within budget\n\n"
    )


RUNNER_ENV_DEFAULTS = {"SPECKIT_PR_PACKET_TIMESTAMP": "2026-07-02T00:00:00Z"}


def runner_env() -> dict[str, str]:
    return runner_invocation.runner_env(defaults=RUNNER_ENV_DEFAULTS)


run_runner = functools.partial(runner_invocation.run_runner, env_defaults=RUNNER_ENV_DEFAULTS)


def helper_request(helper_id: str, inputs: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "request_id": f"test-{helper_id}",
        "helper_id": helper_id,
        "operation": helper_id,
        "mode": "read_only",
        "inputs": inputs or {},
    }


@contextmanager
def helper_project() -> Iterator[Path]:
    """Keep mutable consumer fixtures separate from the immutable plugin source."""
    with tempfile.TemporaryDirectory(prefix="read-only-helper-consumer-") as directory:
        root = Path(directory).resolve()
        (root / ".specify").mkdir()
        yield root


def response_cwd(data: dict[str, object]) -> Path:
    record = data.get("effective_cwd") or data.get("cwd")
    if not isinstance(record, dict):
        return REPO_ROOT
    value = str(record.get("value") or ".")
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


class _ReadOnlyHelperRunner:
    """Shared fixture for the tests below."""

    helper_filter: str | None = None

    def run_plan_layers(
        self,
        feature_dir: str,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object], dict[str, object]]:
        completed, response, stderr_records = run_runner(
            helper_request("plan-layers-feature-dir", {"feature_dir": feature_dir})
        )
        self.assertEqual(completed.returncode, response["exit_code"])
        self.assertEqual(
            [diag["code"] for diag in stderr_records],
            [diag["code"] for diag in response["diagnostics"]],
        )
        planner = response["data"]["stdout_json"]
        self.assertEqual(planner["tool"], "plan-layers")
        self.assertEqual(planner["contract_version"], 1)
        return completed, response, planner


class SpecKitExecutableReuseTests(unittest.TestCase):
    operations = (
        ["integration", "list"],
        ["init", "--here", "--integration", "claude", "--script", "sh"],
        ["init", "--here", "--integration", "codex", "--script", "sh"],
        ["integration", "install", "claude", "--script", "sh"],
        ["integration", "install", "codex", "--script", "sh"],
        ["check"], ["self", "check"],
        ["integration", "upgrade", "claude", "--script", "sh"],
        ["integration", "upgrade", "codex", "--force", "--script", "sh"],
        ["extension", "add", "fixture"], ["preset", "add", "fixture"],
        ["preset", "resolve", "spec-template"],
        ["preset", "resolve", "plan-template"],
        ["preset", "resolve", "tasks-template"], ["extension", "list"],
    )

    def test_rejected_candidates_expose_no_launch_argv_at_any_command_site(self) -> None:
        from speckit_pro_runner.helpers.read_only import spec_kit_cli_state

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            checkout = root / "checkout"
            checkout.mkdir()
            trusted = root / "trusted" / "specify"
            trusted.parent.mkdir()
            trusted.touch()
            trusted.chmod(0o755)
            local = checkout / "specify"
            local.touch()
            local.chmod(0o755)
            windows = checkout / "specify.exe"
            windows.touch()
            windows.chmod(0o755)
            outward = checkout / "outward" / "specify"
            outward.parent.mkdir()
            outward.symlink_to(trusted)
            inward = root / "lookup" / "specify"
            inward.parent.mkdir()
            inward.symlink_to(local)
            alias = root / "checkout-alias"
            alias.symlink_to(checkout, target_is_directory=True)
            cases = (
                ("direct-checkout", local, local),
                ("relative-current-directory", "specify", local),
                ("windows-root-lookup", trusted, windows),
                ("checkout-link-outward", outward, outward),
                ("checkout-link-reselected-external", outward, trusted),
                ("external-link-inward", inward, inward),
                ("checkout-directory-link", alias / "specify", alias / "specify"),
            )
            for platform in ("linux", "win32"):
                for variant, selected, lookup in cases:
                    for operation in self.operations:
                        with self.subTest(platform=platform, variant=variant, operation=operation), patch(
                            "speckit_pro_runner.helpers.read_only.Path.cwd", return_value=checkout,
                        ), patch("speckit_pro_runner.helpers.read_only.sys.platform", platform), patch(
                            "speckit_pro_runner.helpers.read_only.shutil.which", return_value=str(lookup),
                        ), patch("speckit_pro_runner.helpers.read_only.subprocess.run") as run:
                            rows, state = spec_kit_cli_state(str(selected), checkout)
                            self.assertEqual(state["status"], "missing")
                            self.assertFalse(rows[0]["pass"])
                            self.assertEqual(state.get("cli_argv"), [])
                            run.assert_not_called()

    def test_absolute_launch_survives_alias_link_and_rename_replacement(self) -> None:
        from speckit_pro_runner.helpers.read_only import spec_kit_cli_state

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            checkout = root / "checkout"
            checkout.mkdir()
            # A private 0755 stub, not the interpreter: hosted Linux runners ship interpreters
            # with group-write bits, which the trust check rightly rejects.
            trusted = root / "trusted" / "specify"
            trusted.parent.mkdir()
            trusted.touch()
            trusted.chmod(0o755)
            hostile = checkout / "specify.exe"
            hostile.write_text("rejected checkout executable\n", encoding="utf-8")
            hostile.chmod(0o755)
            alias = root / "lookup" / "specify"
            alias.parent.mkdir()
            for platform in ("linux", "win32"):
                for replacement in ("link", "rename"):
                    alias.unlink(missing_ok=True)
                    alias.symlink_to(trusted)
                    with patch("speckit_pro_runner.helpers.read_only.sys.platform", platform), patch(
                        "speckit_pro_runner.helpers.read_only.Path.cwd", return_value=checkout,
                    ), patch(
                        "speckit_pro_runner.helpers.read_only.shutil.which",
                        side_effect=lambda _name, *, path: str(trusted if path == str(trusted.parent) else alias),
                    ), patch(
                        "speckit_pro_runner.helpers.read_only.subprocess.run",
                        return_value=SimpleNamespace(stdout="CLI Version    1.1.0", returncode=0),
                    ):
                        rows, state = spec_kit_cli_state(str(alias), checkout)
                    self.assertTrue(rows[0]["pass"])
                    self.assertEqual(state.get("cli_argv"), [str(trusted)])
                    alias.unlink()
                    if replacement == "link":
                        alias.symlink_to(hostile)
                    else:
                        staged = alias.with_name("replacement")
                        staged.write_bytes(hostile.read_bytes())
                        staged.chmod(0o755)
                        staged.replace(alias)
                    for operation in self.operations:
                        with self.subTest(platform=platform, replacement=replacement, operation=operation):
                            result = subprocess.run(
                                [sys.executable, "-c", "import json, sys; print(json.dumps(sys.argv[1:]))", *operation],
                                cwd=checkout, shell=False,
                                capture_output=True, text=True, check=True,
                                env={**os.environ, "PATH": str(checkout)},
                            )
                            self.assertEqual(json.loads(result.stdout), operation)

    def test_both_hosts_use_verified_argv_for_every_later_spec_kit_launch(self) -> None:
        from speckit_pro_runner.host_skills import render_host_skills

        plugin = Path(__file__).resolve().parents[3] / "speckit-pro"
        with tempfile.TemporaryDirectory() as temporary:
            for host in ("claude", "codex"):
                destination = Path(temporary) / host
                render_host_skills(plugin, host, destination)
                for skill in ("speckit-install", "speckit-upgrade", "speckit-scaffold-spec"):
                    with self.subTest(host=host, skill=skill):
                        text = (destination / skill / "SKILL.md").read_text(encoding="utf-8")
                        self.assertIn("spec_kit.cli_argv", text)
                        self.assertIn("If `cli_argv` is empty, STOP", text)
                        self.assertIn("Re-run `check-prerequisites` after", text)
                        self.assertIn("every Spec Kit command", " ".join(text.split()))
                        self.assertIn("shell=False", text)
                        body = text[text.index("\n---", 4) + 4:]
                        self.assertNotRegex(body, r"`specify\s")

    def test_prerequisite_repair_fields_delegate_to_verified_launch_skills(self) -> None:
        from speckit_pro_runner.helpers.read_only import check_prerequisites

        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary).resolve()
            local = checkout / "specify.exe"
            local.touch()
            local.chmod(0o755)
            skill = checkout / ".claude" / "skills" / "speckit-checklist" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("Run `.specify/scripts/bash/check-prerequisites.sh --template spec`.\n", encoding="utf-8")
            for selected in (local, Path(sys.executable).resolve()):
                with patch("speckit_pro_runner.helpers.read_only.find_specify", return_value=str(selected)), patch(
                    "speckit_pro_runner.helpers.read_only.shutil.which", return_value=str(selected),
                ):
                    report = json.loads(check_prerequisites({"workflow_file": ""}, checkout)["stdout"])
                for name, repair_skill in (("project_init", "speckit-install"),
                                           ("commands", "speckit-install"),
                                           ("setup_contract", "speckit-upgrade")):
                    with self.subTest(accepted=selected != local, field=name):
                        row = next(item for item in report["checks"] if item["check"] == name)
                        self.assertFalse(row["pass"])
                        self.assertNotRegex(row["message"] + row["detail"], r"\bspecify(?:\.exe)?\s+(?:init|integration)")
                        self.assertIn(repair_skill, row["message"])


class ReadOnlyHelperTests(_ReadOnlyHelperRunner, unittest.TestCase):
    def test_validate_agent_install_rejects_invalid_surface_or_loaded_root(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-agent-install":
            self.skipTest("validate-agent-install cases use validate-agent-install")
        for inputs in ({"surface": "codex"}, {"surface": "claude", "plugin_root": "tests"}):
            with self.subTest(inputs=inputs):
                completed, response, stderr_records = run_runner(
                    helper_request("validate-agent-install", inputs)
                )
                self.assertEqual(completed.returncode, 2)
                self.assert_response(response, "input_error", 2)
                self.assertEqual(response["diagnostics"][0]["code"], "invalid_input")
                self.assertEqual(stderr_records, response["diagnostics"])

    def test_validate_agent_install_detects_missing_unexpected_nonregular_and_symlink(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-agent-install":
            self.skipTest("validate-agent-install cases use validate-agent-install")
        from speckit_pro_runner.helpers.read_only import CLAUDE_REQUIRED_AGENT_NAMES, validate_agent_install

        with tempfile.TemporaryDirectory(prefix="validate-agent-install-") as directory:
            plugin_root = Path(directory)
            agents_dir = plugin_root / "agents"
            agents_dir.mkdir()
            omitted = {"phase-executor", "sweep-analyst"}
            for name in CLAUDE_REQUIRED_AGENT_NAMES:
                if name not in omitted:
                    (agents_dir / f"{name}.md").write_text("", encoding="utf-8")
            (agents_dir / "unexpected.md").write_text("", encoding="utf-8")
            (agents_dir / "directory.md").mkdir()
            (agents_dir / "phase-executor.md").symlink_to(plugin_root / "target.txt")

            with patch("speckit_pro_runner.helpers.read_only.detect_plugin_root", return_value=plugin_root):
                result = validate_agent_install({"surface": "claude"}, REPO_ROOT)

        self.assertEqual(result["exit_code"], 1)
        payload = json.loads(result["stdout"])
        self.assertFalse(payload["valid"])
        self.assertEqual(payload["missing"], ["phase-executor.md", "sweep-analyst.md"])
        self.assertEqual(payload["unexpected"], ["unexpected.md"])
        self.assertEqual(payload["nonregular"], ["directory.md"])
        self.assertEqual(payload["symlinks"], ["phase-executor.md"])

    def test_validate_agent_install_accepts_valid_external_package(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-agent-install":
            self.skipTest("validate-agent-install cases use validate-agent-install")
        from speckit_pro_runner.helpers.read_only import CLAUDE_REQUIRED_AGENT_NAMES, validate_agent_install

        with tempfile.TemporaryDirectory(prefix="validate-agent-install-") as directory:
            plugin_root = Path(directory)
            agents_dir = plugin_root / "agents"
            agents_dir.mkdir()
            for name in CLAUDE_REQUIRED_AGENT_NAMES:
                (agents_dir / f"{name}.md").write_text("", encoding="utf-8")
            with patch("speckit_pro_runner.helpers.read_only.detect_plugin_root", return_value=plugin_root):
                result = validate_agent_install({"surface": "claude"}, REPO_ROOT)

        payload = json.loads(result["stdout"])
        self.assertEqual(result["exit_code"], 0)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["missing"], [])
        self.assertEqual(payload["unexpected"], [])
        self.assertEqual(payload["nonregular"], [])
        self.assertEqual(payload["symlinks"], [])

    def test_validate_agent_install_rejects_symlink_agent_directory_and_matches_source_roster(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-agent-install":
            self.skipTest("validate-agent-install cases use validate-agent-install")
        from speckit_pro_runner.helpers.read_only import CLAUDE_REQUIRED_AGENT_NAMES, validate_agent_install

        from speckit_pro_runner.agent_inventory import (
            CLAUDE_REQUIRED_AGENT_NAMES as INVENTORY_CLAUDE_REQUIRED_AGENT_NAMES,
        )

        self.assertEqual(INVENTORY_CLAUDE_REQUIRED_AGENT_NAMES, CLAUDE_REQUIRED_AGENT_NAMES)

        with tempfile.TemporaryDirectory(prefix="validate-agent-install-") as directory:
            plugin_root = Path(directory)
            real_agents_dir = plugin_root / "real-agents"
            real_agents_dir.mkdir()
            (plugin_root / "agents").symlink_to(real_agents_dir, target_is_directory=True)
            with patch("speckit_pro_runner.helpers.read_only.detect_plugin_root", return_value=plugin_root):
                result = validate_agent_install({"surface": "claude"}, REPO_ROOT)

        self.assertEqual(result["exit_code"], 3)
        self.assertEqual(json.loads(result["stdout"]), {"error": "loaded Claude agent directory is unavailable"})

    @property
    def packet_root(self) -> Path:
        """Own packet inputs without making the shipped plugin writable."""
        if not hasattr(self, "_packet_root"):
            temporary = tempfile.TemporaryDirectory(prefix="pr-packet-consumer-")
            self.addCleanup(temporary.cleanup)
            root = Path(temporary.name).resolve()
            (root / ".specify").mkdir()
            (root / "scratch").mkdir()
            shutil.copytree(PR_PACKET_FIXTURE_DIR, root / PR_PACKET_FIXTURE_DIR.relative_to(REPO_ROOT))
            self._packet_root = root
        return self._packet_root

    @property
    def packet_fixture_dir(self) -> Path:
        return self.packet_root / PR_PACKET_FIXTURE_DIR.relative_to(REPO_ROOT)

    def run_packet_runner(
        self, request: object, *, cwd: Path | None = None
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object], list[dict[str, object]]]:
        return run_runner(request, cwd=self.packet_root if cwd is None else cwd)

    def test_packet_consumer_copies_exact_fixtures_and_cleans_up(self) -> None:
        consumer = ReadOnlyHelperTests()
        try:
            root = consumer.packet_root
            self.assertFalse(root.is_relative_to(REPO_ROOT))
            expected = {path.relative_to(PR_PACKET_FIXTURE_DIR): path.read_bytes()
                        for path in PR_PACKET_FIXTURE_DIR.rglob("*") if path.is_file()}
            observed = {path.relative_to(consumer.packet_fixture_dir): path.read_bytes()
                        for path in consumer.packet_fixture_dir.rglob("*") if path.is_file()}
            self.assertEqual(observed, expected)
            self.assertFalse((root / "speckit-pro").exists())
        finally:
            consumer.doCleanups()
        self.assertFalse(root.exists())

    def test_helper_project_is_isolated_and_cleans_up_on_failure(self) -> None:
        with helper_project() as root:
            self.assertFalse(root.is_relative_to(REPO_ROOT))
            self.assertTrue((root / ".specify").is_dir())
        self.assertFalse(root.exists())
        materialized: list[Path] = []

        def run_failing_body() -> None:
            with helper_project() as failed_root:
                materialized.append(failed_root)
                raise RuntimeError("consumer cleanup probe")

        self.assertRaisesRegex(RuntimeError, "consumer cleanup probe", run_failing_body)
        self.assertFalse(materialized[0].exists())

    def build_binding_worktrees(self, base: Path) -> tuple[Path, Path, Path]:
        task_root = base / "repo"
        descendant_root = task_root / ".worktrees" / "nested"
        external_root = base / "external"
        task_root.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main", str(task_root)],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(task_root), "config", "user.email", "support@openai.com"],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(task_root), "config", "user.name", "SpecKit Tests"],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(task_root), "config", "commit.gpgsign", "false"],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        (task_root / "seed.txt").write_text("seed\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(task_root), "add", "seed.txt"],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(task_root), "commit", "-m", "seed"],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(task_root), "worktree", "add", "-b", "nested", str(descendant_root)],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(task_root), "worktree", "add", "-b", "external", str(external_root)],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        return task_root, descendant_root, external_root

    def binding_result(self, task_root: Path, workflow_file: str) -> tuple[dict[str, object], int]:
        from speckit_pro_runner.helpers.read_only import resolve_workflow_binding

        result = resolve_workflow_binding({"workflow_file": workflow_file}, task_root)
        return json.loads(result["stdout"]), int(result["exit_code"])

    def build_scaffold_placement_worktrees(
        self,
        base: Path,
        *,
        ignore_worktrees: bool = True,
    ) -> tuple[Path, Path]:
        primary_root = base / "Documents" / "Projects" / "racecraft-plugins-private"
        task_root = base / ".codex" / "worktrees" / "15bd" / "racecraft-plugins-private"
        primary_root.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "-b", "main", str(primary_root)],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        for key, value in (
            ("user.email", "support@openai.com"),
            ("user.name", "SpecKit Tests"),
            ("commit.gpgsign", "false"),
        ):
            subprocess.run(
                ["git", "-C", str(primary_root), "config", key, value],
                text=True,
                capture_output=True,
                shell=False,
                check=True,
            )
        (primary_root / "seed.txt").write_text("seed\n", encoding="utf-8")
        (primary_root / ".specify").mkdir()
        (primary_root / ".specify" / "fixture.txt").write_text("fixture\n", encoding="utf-8")
        if ignore_worktrees:
            (primary_root / ".gitignore").write_text("/.worktrees/\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(primary_root), "add", "."],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(primary_root), "commit", "-m", "seed"],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        task_root.parent.mkdir(parents=True)
        subprocess.run(
            ["git", "-C", str(primary_root), "worktree", "add", "--detach", str(task_root)],
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        return primary_root, task_root

    def placement_result(
        self,
        task_root: Path,
        branch_name: str,
        *,
        worktree_root_override: str | None = None,
    ) -> tuple[dict[str, object], int]:
        from speckit_pro_runner.helpers.read_only import resolve_scaffold_worktree_placement

        inputs: dict[str, object] = {"branch_name": branch_name}
        if worktree_root_override is not None:
            inputs["worktree_root_override"] = worktree_root_override
        result = resolve_scaffold_worktree_placement(inputs, task_root)
        return json.loads(result["stdout"]), int(result["exit_code"])

    def assert_response(self, response: dict[str, object], status: str, exit_code: int) -> None:
        assert_runner_response(self, response, status, exit_code)

    def filtered_helpers(self) -> list[str]:
        if self.helper_filter:
            self.assertIn(self.helper_filter, EXPECTED_HELPERS)
            return [self.helper_filter]
        return EXPECTED_HELPERS

    def assert_helper_matches_bash_reference(
        self, helper_id: str, inputs: dict[str, object], *, cwd: Path = REPO_ROOT
    ) -> dict[str, object]:
        completed, response, stderr_records = run_runner(helper_request(helper_id, inputs), cwd=cwd)
        data = response["data"]
        self.assertEqual(data["shell"], False)
        self.assertEqual(data["argv"][-2:], ["-m", "speckit_pro_runner"])
        self.assertEqual(data["python_operation"], helper_id)
        self.assertTrue(data["authoritative_command"].endswith("| python -m speckit_pro_runner"))
        self.assertEqual(completed.returncode, response["exit_code"])
        self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])
        return response

    def assert_stdout_matches_reference(self, helper_id: str, actual: str, expected: str) -> None:
        if helper_id not in JSON_STDOUT_PARITY_HELPERS:
            self.assertEqual(actual, expected)
            return
        try:
            actual_json = json.loads(actual)
            expected_json = json.loads(expected)
        except json.JSONDecodeError as exc:
            self.fail(f"FAIL detail: {helper_id} stdout must be valid JSON: {exc}; actual={actual!r}; expected={expected!r}")
        self.assertEqual(
            actual_json,
            expected_json,
            f"FAIL detail: {helper_id} JSON stdout mismatch: actual_json={actual_json!r}; expected_json={expected_json!r}; actual={actual!r}; expected={expected!r}",
        )

    def test_replay_command_is_runnable_from_an_install(self) -> None:
        if self.helper_filter and self.helper_filter != "generate-spec-index-check":
            self.skipTest("replay command test uses generate-spec-index-check")
        _completed, response, _stderr_records = run_runner(
            helper_request("generate-spec-index-check", HELPER_CASES["generate-spec-index-check"])
        )
        data = response["data"]
        command = data["authoritative_command"]
        self.assertNotIn("tests/", command)
        words = shlex.split(command)
        self.assertEqual(words[:2], ["printf", "%s"])
        self.assertEqual(words[3:], ["|", "python", "-m", "speckit_pro_runner"])
        self.assertEqual(json.loads(words[2]), data["stdin_request"])

    def test_registry_dispatch_lists_only_read_only_helpers(self) -> None:
        if self.helper_filter and self.helper_filter != "helper-registry-dispatch":
            self.skipTest("registry test is not part of this helper filter")
        completed, response, stderr_records = run_runner(helper_request("helper-registry-dispatch"))
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(stderr_records, [])
        self.assert_response(response, "ok", 0)
        data = response["data"]
        helpers = data["helpers"]
        helper_ids = [record["helper_id"] for record in helpers]
        self.assertEqual(helper_ids, sorted(EXPECTED_HELPERS))
        self.assertEqual(data["mutation_modes_promoted"], [])
        for record in helpers:
            self.assertEqual(record["mode"], "read_only")
            self.assertIn(record["promotion_status"], {"python_authoritative", "bash_reference_only", "out_of_scope"})
            self.assertEqual(record["python_operation"], record["operation"])
            self.assertNotIn("script", record)
            self.assertNotIn("generate-pr-body", str(record))
            self.assertNotIn("restack.sh", str(record))
            active_record = {key: value for key, value in record.items() if key != "inactive_provenance"}
            self.assertNotIn(".sh", json.dumps(active_record, sort_keys=True))
            self.assertNotIn("authoritative_command", record)
            self.assertNotIn("tests/", json.dumps(record))
            fixture_command = registry.HELPERS[record["helper_id"]].authoritative_command
            fixture_path = command_stdin_fixture(fixture_command)
            self.assertTrue(fixture_path.is_file(), fixture_command)
            request = json.loads(fixture_path.read_text(encoding="utf-8"))
            self.assertEqual(request["helper_id"], record["helper_id"])
            self.assertEqual(request["operation"], record["operation"])

    def test_render_plan_repair_context_binds_exact_sources_and_g3_envelope(self) -> None:
        if self.helper_filter and self.helper_filter != "render-plan-repair-context":
            self.skipTest("Plan-repair rendering cases use render-plan-repair-context")
        completed, response, stderr_records = run_runner(
            helper_request("render-plan-repair-context", HELPER_CASES["render-plan-repair-context"])
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(stderr_records, [])
        self.assert_response(response, "ok", 0)
        rendered = response["data"]["stdout_json"]
        self.assertEqual(rendered["schema"], "plan-repair-executor-message/v1")
        message = rendered["executor_message"]
        for name in ("plan-repair-original.md", "plan-repair-source.md"):
            exact = (FIXTURE_DIR / name).read_text(encoding="utf-8")
            self.assertIn(exact, message)
        attempts = json.loads((FIXTURE_DIR / "plan-repair-attempts.json").read_text(encoding="utf-8"))
        decoder = json.JSONDecoder()
        embedded = []
        for index, character in enumerate(message):
            if character not in "{[":
                continue
            try:
                candidate, _end = decoder.raw_decode(message, index)
            except json.JSONDecodeError:
                continue
            embedded.append(candidate)
        self.assertIn(attempts["attempts"][0], embedded)
        encoded = message.encode("utf-8")
        self.assertEqual(rendered["message_bytes"], len(encoded))
        self.assertEqual(rendered["message_sha256"], hashlib.sha256(encoded).hexdigest())
        self.assertRegex(rendered["context_bundle_sha256"], r"\A[a-f0-9]{64}\Z")
        self.assertEqual(
            message.count(
                "PLAN_REPAIR_CONTEXT_SHA256=" + rendered["context_bundle_sha256"]
            ),
            1,
        )
        self.assertEqual(
            rendered["context_ids"], ["original-plan-prompt", "source-evidence"],
        )

    def test_render_plan_repair_context_fails_closed_on_untrusted_or_malformed_evidence(self) -> None:
        if self.helper_filter and self.helper_filter != "render-plan-repair-context":
            self.skipTest("Plan-repair rendering cases use render-plan-repair-context")
        traversal = dict(HELPER_CASES["render-plan-repair-context"])
        traversal["context_paths"] = {"source-evidence": "../outside.md"}
        completed, response, stderr_records = run_runner(
            helper_request("render-plan-repair-context", traversal)
        )
        self.assertEqual(completed.returncode, 2)
        self.assert_response(response, "input_error", 2)
        self.assertEqual([row["code"] for row in stderr_records], ["unsupported_path"])

        with helper_project() as root:
            (root / "context.md").write_text("trusted source\n", encoding="utf-8")
            (root / "attempts.json").write_text(
                '{"attempts":[],"attempts":[]}\n', encoding="utf-8",
            )
            malformed = {
                **HELPER_CASES["render-plan-repair-context"],
                "context_paths": {"source-evidence": "context.md"},
                "g3_attempts_path": "attempts.json",
            }
            completed, response, stderr_records = run_runner(
                helper_request("render-plan-repair-context", malformed), cwd=root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual(response["data"]["stdout_json"]["error"], "G3 attempts evidence is malformed")
            self.assertEqual([row["code"] for row in stderr_records], ["invalid_input"])

    def test_envelope_rejects_unknown_and_mutation_modes(self) -> None:
        if self.helper_filter:
            self.skipTest("envelope rejection test is registry-level")
        cases = [
            (helper_request("not-a-helper"), "unknown_helper", 2),
            ({**helper_request("count-markers"), "mode": "write"}, "invalid_envelope", 2),
            ({**helper_request("count-markers"), "operation": "other"}, "helper_operation_mismatch", 2),
        ]
        for request, code, exit_code in cases:
            with self.subTest(code=code):
                completed, response, stderr_records = run_runner(request)
                self.assertEqual(completed.returncode, exit_code)
                self.assert_response(response, "input_error", exit_code)
                self.assertEqual([diag["code"] for diag in response["diagnostics"]], [code])
                self.assertEqual([diag["code"] for diag in stderr_records], [code])

    def test_write_mode_diagnostic_names_registered_mutation_operation(self) -> None:
        if self.helper_filter:
            self.skipTest("write-mode remediation is registry-level")
        cases = [
            (
                "generate-spec-index-check",
                {"write_mode": True},
                "Submit a separate runner request with helper_id and operation generate-spec-index-write.",
            ),
            (
                "count-markers",
                {"type": "all", "feature_dir": FEATURE_DIR, "write_mode": True},
                "Inspect mutation-registry-dispatch for a registered Python mutation operation.",
            ),
            (
                "plan-layers-feature-dir",
                {"feature_dir": FEATURE_DIR, "write_mode": True},
                "The registered plan-layers-marker-plan operation remains deferred; keep this request read_only.",
            ),
            (
                "validate-pr-packet-read-only",
                {**HELPER_CASES["validate-pr-packet-read-only"], "write_mode": True},
                "Submit a separate runner request with helper_id and operation validate-pr-packet-write.",
            ),
        ]
        for helper_id, inputs, mutation_action in cases:
            with self.subTest(helper_id=helper_id):
                completed, response, stderr_records = run_runner(helper_request(helper_id, inputs))
                self.assertEqual(completed.returncode, 2)
                self.assert_response(response, "input_error", 2)
                diagnostic = response["diagnostics"][0]
                self.assertEqual(diagnostic["code"], "unsupported_mode")
                self.assertEqual(
                    diagnostic["remediation"]["actions"],
                    ["Remove write_mode from the request.", mutation_action],
                )
                self.assertNotIn("Bash", json.dumps(diagnostic, sort_keys=True))
                self.assertEqual(stderr_records, response["diagnostics"])

    def test_active_error_output_uses_registered_operation_names(self) -> None:
        if self.helper_filter:
            self.skipTest("active output regression is cross-helper")
        from speckit_pro_runner.helpers.read_only import (
            confidence_gate,
            count_markers,
            validate_pr_packet_read_only,
            validate_pr_workflow_contract,
        )

        cases = [
            (
                count_markers({}, REPO_ROOT),
                '{"error":"Usage: count-markers <gaps|findings|clarifications|all> <feature_dir>"}\n',
                "",
                2,
            ),
            (
                confidence_gate({}, REPO_ROOT),
                '{"error":"Usage: confidence-gate <workflow-file> [--threshold N.NN] [--mode advisory|strict]"}\n',
                "",
                1,
            ),
            (
                validate_pr_workflow_contract({}, REPO_ROOT),
                "",
                "validate-pr-workflow-contract: input_error: missing required option --title\n",
                2,
            ),
            (
                validate_pr_packet_read_only({}, REPO_ROOT),
                None,
                "validate-pr-packet-read-only: input_error: missing-packet-path: input.error: no-path\n",
                2,
            ),
        ]
        for result, stdout, stderr, exit_code in cases:
            with self.subTest(stderr=stderr):
                if stdout is not None:
                    self.assertEqual(result["stdout"], stdout)
                self.assertEqual(result["stderr"], stderr)
                self.assertEqual(result["exit_code"], exit_code)
                self.assertNotIn(".sh", result["stdout"] + result["stderr"])

    def test_fixture_manifests_cover_registered_helpers(self) -> None:
        if self.helper_filter and self.helper_filter != "helper-registry-dispatch":
            self.skipTest("manifest coverage test is registry-level")
        fixture_manifest = json.loads((FIXTURE_DIR / "fixture-manifest.json").read_text(encoding="utf-8"))
        fixture_ids = [record["helper_id"] for record in fixture_manifest["helpers"]]
        self.assertEqual(fixture_ids, EXPECTED_HELPERS)
        for record in fixture_manifest["helpers"]:
            for field in (
                "promotion_status",
                "failure_classes",
                "rejected_stdout_schema",
                "deterministic_remediation",
                "subprocess_policy",
                "path_boundary_policy",
                "authoritative_command",
                "rollback",
            ):
                self.assertIn(field, record)
            self.assertEqual(record["subprocess_policy"]["shell"], False)
            self.assertTrue(record["deterministic_remediation"]["actions"])
            active_guidance = json.dumps(
                {
                    "deterministic_remediation": record["deterministic_remediation"],
                    "rollback": record["rollback"],
                },
                sort_keys=True,
            )
            self.assertNotIn(".sh", active_guidance)
            self.assertNotIn("bash", active_guidance.lower())
            fixture_path = command_stdin_fixture(record["authoritative_command"])
            self.assertTrue(fixture_path.is_file(), record["authoritative_command"])
            request = json.loads(fixture_path.read_text(encoding="utf-8"))
            self.assertEqual(request["helper_id"], record["helper_id"])
            self.assertEqual(request["operation"], record["operation"])

    def test_path_boundary_rejects_traversal_and_symlink_escape(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("path-boundary cases use check-prerequisites")
        with helper_project() as inside, tempfile.TemporaryDirectory() as outside:
            outside_file = Path(outside) / "outside-workflow.md"
            outside_file.write_text("# outside\n", encoding="utf-8")
            symlink_path = inside / "escape.md"
            try:
                symlink_path.symlink_to(outside_file)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            cases = [
                "../outside.md",
                symlink_path.relative_to(inside).as_posix(),
            ]
            for workflow_file in cases:
                with self.subTest(workflow_file=workflow_file):
                    completed, response, stderr_records = run_runner(
                        helper_request("check-prerequisites", {"workflow_file": workflow_file}), cwd=inside
                    )
                    self.assertEqual(completed.returncode, 2)
                    self.assert_response(response, "input_error", 2)
                    self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["unsupported_path"])
                    self.assertEqual([diag["code"] for diag in stderr_records], ["unsupported_path"])

    def test_resolve_workflow_binding_covers_registered_worktree_relations(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        with tempfile.TemporaryDirectory() as temp:
            task_root, descendant_root, external_root = self.build_binding_worktrees(Path(temp))

            same_file = task_root / "same-workflow.md"
            same_file.write_text("# same\n", encoding="utf-8")
            payload, exit_code = self.binding_result(task_root, same_file.name)
            self.assertEqual((payload["binding_status"], payload["relation"], exit_code), ("resolved", "same", 0))
            self.assertEqual(payload["workflow_root"], task_root.resolve().as_posix())

            nested_file = descendant_root / "nested-workflow.md"
            nested_file.write_text("# nested\n", encoding="utf-8")
            payload, exit_code = self.binding_result(task_root, nested_file.name)
            self.assertEqual(
                (payload["binding_status"], payload["relation"], exit_code),
                ("resolved", "descendant", 0),
            )
            self.assertEqual(payload["workflow_root"], descendant_root.resolve().as_posix())

            nested_relative = descendant_root.relative_to(task_root) / nested_file.name
            payload, exit_code = self.binding_result(task_root, nested_relative.as_posix())
            self.assertEqual(
                (payload["binding_status"], payload["relation"], exit_code),
                ("resolved", "descendant", 0),
            )
            self.assertEqual(payload["workflow_root"], descendant_root.resolve().as_posix())

            rebound, exit_code = self.binding_result(descendant_root, str(nested_file))
            self.assertEqual(
                (rebound["binding_status"], rebound["relation"], exit_code),
                ("resolved", "same", 0),
            )
            self.assertEqual(rebound["task_root"], descendant_root.resolve().as_posix())
            self.assertEqual(rebound["workflow_root"], descendant_root.resolve().as_posix())
            self.assertEqual(rebound["workflow_file"], nested_file.resolve().as_posix())

            external_file = external_root / "external-workflow.md"
            external_file.write_text("# external\n", encoding="utf-8")
            payload, exit_code = self.binding_result(task_root, external_file.name)
            self.assertEqual(
                (payload["binding_status"], payload["relation"], exit_code),
                ("resolved", "external", 0),
            )
            self.assertEqual(payload["workflow_root"], external_root.resolve().as_posix())

    def test_resolve_workflow_binding_binds_explicit_sibling_worktree_without_touching_task_root(self) -> None:
        # Codex prerequisites bind an explicit absolute sibling workflow in the same task (issue 656).
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        with tempfile.TemporaryDirectory() as temp:
            # A canonical base keeps the explicit path free of temp-directory symlink aliases.
            task_root, _, sibling_root = self.build_binding_worktrees(Path(temp).resolve())
            workflow = sibling_root / "docs" / "ai" / "specs" / ".process" / "DEMO-001-workflow.md"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("# demo\n", encoding="utf-8")
            shared = Path("shared-workflow.md")
            (task_root / shared).write_text("# task\n", encoding="utf-8")
            (sibling_root / shared).write_text("# sibling\n", encoding="utf-8")

            def task_state() -> tuple[str, str]:
                def git(*args: str) -> str:
                    return subprocess.run(
                        ["git", "-C", str(task_root), *args],
                        text=True, capture_output=True, shell=False, check=True,
                    ).stdout
                return git("rev-parse", "--abbrev-ref", "HEAD"), git("status", "--porcelain")

            before = task_state()
            payload, exit_code = self.binding_result(task_root, str(workflow))
            self.assertEqual(
                (payload["binding_status"], payload["relation"], exit_code),
                ("resolved", "external", 0),
            )
            self.assertEqual(payload["task_root"], task_root.resolve().as_posix())
            self.assertEqual(payload["workflow_root"], sibling_root.resolve().as_posix())
            self.assertEqual(payload["workflow_file"], workflow.resolve().as_posix())
            self.assertEqual(task_state(), before)

            revalidated, exit_code = self.binding_result(sibling_root, payload["workflow_file"])
            self.assertEqual(
                (revalidated["binding_status"], revalidated["relation"], exit_code),
                ("resolved", "same", 0),
            )
            self.assertEqual(revalidated["task_root"], payload["workflow_root"])
            self.assertEqual(revalidated["workflow_root"], payload["workflow_root"])
            self.assertEqual(revalidated["workflow_file"], payload["workflow_file"])

            ambiguous, exit_code = self.binding_result(task_root, shared.as_posix())
            self.assertEqual((ambiguous["binding_status"], exit_code), ("ambiguous", 1))
            self.assertIsNone(ambiguous["workflow_root"])
            self.assertIsNone(ambiguous["relation"])
            self.assertEqual(
                ambiguous["candidates"],
                sorted([task_root.resolve().as_posix(), sibling_root.resolve().as_posix()]),
            )
            self.assertEqual(task_state(), before)

    def test_resolve_workflow_binding_binds_explicit_path_through_symlinked_parent_directory(self) -> None:
        # A symlinked spelling of a worktree's parent directory, such as macOS /tmp, binds like the real path (issue 702).
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            real_base = base / "real"
            real_base.mkdir()
            task_root, _, sibling_root = self.build_binding_worktrees(real_base)
            workflow = sibling_root / "docs" / "ai" / "specs" / ".process" / "DEMO-001-workflow.md"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("# demo\n", encoding="utf-8")
            alias_base = base / "alias"
            try:
                alias_base.symlink_to(real_base, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            aliased_workflow = alias_base / workflow.relative_to(real_base)

            real_payload, real_exit = self.binding_result(task_root, str(workflow))
            payload, exit_code = self.binding_result(task_root, str(aliased_workflow))

            self.assertEqual(
                (payload["binding_status"], payload["relation"], exit_code),
                ("resolved", "external", 0),
            )
            self.assertEqual((payload, exit_code), (real_payload, real_exit))
            self.assertEqual(payload["workflow_root"], sibling_root.resolve().as_posix())
            self.assertEqual(payload["workflow_file"], workflow.resolve().as_posix())

            aliased_task, exit_code = self.binding_result(alias_base / task_root.name, str(aliased_workflow))
            self.assertEqual((aliased_task, exit_code), (real_payload, real_exit))

    def test_resolve_workflow_binding_rejects_escape_through_symlinked_parent_directory(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            real_base = base / "real"
            real_base.mkdir()
            task_root, _, sibling_root = self.build_binding_worktrees(real_base)
            outside = base / "outside-workflow.md"
            outside.write_text("# outside\n", encoding="utf-8")
            escape = sibling_root / "escape-workflow.md"
            alias_base = base / "alias"
            root_alias = base / "root-alias"
            try:
                escape.symlink_to(outside)
                alias_base.symlink_to(real_base, target_is_directory=True)
                root_alias.symlink_to(sibling_root, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            (sibling_root / "aliased-workflow.md").write_text("# sibling\n", encoding="utf-8")

            for supplied in (
                alias_base / escape.relative_to(real_base),
                root_alias / "aliased-workflow.md",
            ):
                with self.subTest(supplied=supplied.relative_to(base).as_posix()):
                    payload, exit_code = self.binding_result(task_root, str(supplied))
                    self.assertEqual((payload["binding_status"], exit_code), ("invalid", 1))
                    self.assertIsNone(payload["workflow_root"])
                    self.assertIsNone(payload["workflow_file"])

    def test_resolve_scaffold_placement_anchors_to_detached_task_root_and_revalidates(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-scaffold-worktree-placement":
            self.skipTest("scaffold-placement cases use resolve-scaffold-worktree-placement")
        with tempfile.TemporaryDirectory() as temp:
            primary_root, task_root = self.build_scaffold_placement_worktrees(Path(temp))
            branch = "fixture-dual-runtime-writing-boundary"
            expected_root = task_root / ".worktrees" / branch

            worktree_listing = subprocess.run(
                ["git", "-C", str(task_root), "worktree", "list", "--porcelain"],
                text=True,
                capture_output=True,
                shell=False,
                check=True,
            ).stdout
            self.assertTrue(worktree_listing.startswith(f"worktree {primary_root.resolve()}\n"))
            common_dir_text = subprocess.run(
                ["git", "-C", str(task_root), "rev-parse", "--git-common-dir"],
                text=True,
                capture_output=True,
                shell=False,
                check=True,
            ).stdout.strip()
            common_dir = Path(common_dir_text)
            if not common_dir.is_absolute():
                common_dir = task_root / common_dir
            self.assertEqual(common_dir.resolve(), (primary_root / ".git").resolve())

            payload, exit_code = self.placement_result(task_root, branch)
            self.assertEqual(
                (payload["placement_status"], payload["disposition"], payload["relation"], exit_code),
                ("resolved", "create", "descendant", 0),
            )
            self.assertEqual(payload["task_root"], task_root.resolve().as_posix())
            self.assertEqual(payload["worktree_root"], expected_root.resolve().as_posix())
            self.assertNotEqual(payload["worktree_root"], (primary_root / ".worktrees" / branch).as_posix())

            runner_completed = subprocess.run(
                [sys.executable, "-m", "speckit_pro_runner"],
                input=json.dumps(
                    helper_request(
                        "resolve-scaffold-worktree-placement",
                        {"branch_name": branch},
                    )
                ),
                text=True,
                capture_output=True,
                cwd=task_root,
                env=runner_env(),
                shell=False,
                check=False,
            )
            self.assertEqual(runner_completed.returncode, 0, runner_completed.stderr)
            runner_response = json.loads(runner_completed.stdout)
            runner_payload = runner_response["data"]["stdout_json"]
            self.assertEqual(runner_payload["task_root"], task_root.resolve().as_posix())
            self.assertEqual(runner_payload["worktree_root"], expected_root.resolve().as_posix())
            self.assertEqual(runner_payload["relation"], "descendant")

            expected_root.parent.mkdir(parents=True)
            subprocess.run(
                ["git", "-C", str(task_root), "worktree", "add", "-b", branch, str(expected_root)],
                text=True,
                capture_output=True,
                shell=False,
                check=True,
            )

            payload, exit_code = self.placement_result(task_root, branch)
            self.assertEqual(
                (payload["placement_status"], payload["disposition"], payload["relation"], exit_code),
                ("resolved", "reuse", "descendant", 0),
            )
            self.assertEqual(payload["worktree_root"], expected_root.resolve().as_posix())

            payload, exit_code = self.placement_result(expected_root, branch)
            self.assertEqual(
                (payload["placement_status"], payload["disposition"], payload["relation"], exit_code),
                ("resolved", "reuse", "same", 0),
            )
            self.assertEqual(payload["task_root"], expected_root.resolve().as_posix())
            self.assertEqual(payload["worktree_root"], expected_root.resolve().as_posix())

    def test_resolve_scaffold_placement_classifies_existing_and_overridden_external_roots(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-scaffold-worktree-placement":
            self.skipTest("scaffold-placement cases use resolve-scaffold-worktree-placement")
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            primary_root, task_root = self.build_scaffold_placement_worktrees(base)
            sibling_branch = "fixture-existing-sibling"
            sibling_root = base / "existing-sibling-worktree"
            subprocess.run(
                ["git", "-C", str(primary_root), "worktree", "add", "-b", sibling_branch, str(sibling_root)],
                text=True,
                capture_output=True,
                shell=False,
                check=True,
            )

            payload, exit_code = self.placement_result(task_root, sibling_branch)
            self.assertEqual(
                (payload["placement_status"], payload["disposition"], payload["relation"], exit_code),
                ("resolved", "reuse", "external", 0),
            )
            self.assertEqual(payload["worktree_root"], sibling_root.resolve().as_posix())

            override_parent = base / "explicit-external-parent"
            override_branch = "fixture-explicit-external"
            payload, exit_code = self.placement_result(
                task_root,
                override_branch,
                worktree_root_override=str(override_parent),
            )
            self.assertEqual(
                (payload["placement_status"], payload["disposition"], payload["relation"], exit_code),
                ("resolved", "create", "external", 0),
            )
            self.assertEqual(payload["worktree_root"], (override_parent / override_branch).resolve().as_posix())

    def test_resolve_scaffold_placement_rejects_unignored_occupied_symlinked_and_traversal_targets(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-scaffold-worktree-placement":
            self.skipTest("scaffold-placement cases use resolve-scaffold-worktree-placement")

        with tempfile.TemporaryDirectory() as temp:
            _, task_root = self.build_scaffold_placement_worktrees(Path(temp), ignore_worktrees=False)
            payload, exit_code = self.placement_result(task_root, "fixture-unignored")
            self.assertEqual((payload["placement_status"], exit_code), ("conflict", 1))
            self.assertTrue(any("ignored" in problem for problem in payload["problems"]))
            self.assertTrue(any("speckit-install" in problem and "speckit-upgrade" in problem for problem in payload["problems"]))

        with tempfile.TemporaryDirectory() as temp:
            _, task_root = self.build_scaffold_placement_worktrees(Path(temp))
            branch = "fixture-occupied"
            occupied = task_root / ".worktrees" / branch
            occupied.mkdir(parents=True)
            (occupied / "foreign.txt").write_text("occupied\n", encoding="utf-8")
            payload, exit_code = self.placement_result(task_root, branch)
            self.assertEqual((payload["placement_status"], exit_code), ("conflict", 1))
            self.assertTrue(any("occupied" in problem for problem in payload["problems"]))

        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            _, task_root = self.build_scaffold_placement_worktrees(base)
            branch = "fixture-symlinked"
            target = task_root / ".worktrees" / branch
            target.parent.mkdir(parents=True)
            outside = base / "symlink-target"
            outside.mkdir()
            try:
                target.symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            payload, exit_code = self.placement_result(task_root, branch)
            self.assertEqual((payload["placement_status"], exit_code), ("conflict", 1))
            self.assertTrue(any("symlink" in problem for problem in payload["problems"]))

        with tempfile.TemporaryDirectory() as temp:
            _, task_root = self.build_scaffold_placement_worktrees(Path(temp))
            payload, exit_code = self.placement_result(
                task_root,
                "fixture-traversal",
                worktree_root_override="../outside",
            )
            self.assertEqual((payload["placement_status"], exit_code), ("invalid", 1))
            self.assertTrue(any("traversal" in problem for problem in payload["problems"]))

            payload, exit_code = self.placement_result(task_root, "rdl/015-not-single-segment")
            self.assertEqual((payload["placement_status"], exit_code), ("invalid", 1))
            self.assertTrue(any("single segment" in problem for problem in payload["problems"]))

    def test_resolve_scaffold_placement_rejects_branch_path_mismatch_and_prunable_registration(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-scaffold-worktree-placement":
            self.skipTest("scaffold-placement cases use resolve-scaffold-worktree-placement")

        with tempfile.TemporaryDirectory() as temp:
            _, task_root = self.build_scaffold_placement_worktrees(Path(temp))
            requested_branch = "fixture-mismatched"
            mismatched_root = task_root / ".worktrees" / requested_branch
            mismatched_root.parent.mkdir(parents=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(task_root),
                    "worktree",
                    "add",
                    "-b",
                    "different-registered-branch",
                    str(mismatched_root),
                ],
                text=True,
                capture_output=True,
                shell=False,
                check=True,
            )
            payload, exit_code = self.placement_result(task_root, requested_branch)
            self.assertEqual((payload["placement_status"], exit_code), ("conflict", 1))
            self.assertTrue(any("branch/path mismatch" in problem for problem in payload["problems"]))

        with tempfile.TemporaryDirectory() as temp:
            _, task_root = self.build_scaffold_placement_worktrees(Path(temp))
            branch = "fixture-prunable"
            prunable_root = task_root / ".worktrees" / branch
            prunable_root.parent.mkdir(parents=True)
            subprocess.run(
                ["git", "-C", str(task_root), "worktree", "add", "-b", branch, str(prunable_root)],
                text=True,
                capture_output=True,
                shell=False,
                check=True,
            )
            shutil.rmtree(prunable_root)
            listing = subprocess.run(
                ["git", "-C", str(task_root), "worktree", "list", "--porcelain"],
                text=True,
                capture_output=True,
                shell=False,
                check=True,
            ).stdout
            self.assertIn("prunable", listing)
            payload, exit_code = self.placement_result(task_root, branch)
            self.assertEqual((payload["placement_status"], exit_code), ("conflict", 1))
            self.assertTrue(any("prunable" in problem for problem in payload["problems"]))

    def test_registered_worktree_entries_ignores_only_explicitly_prunable_entries(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        from speckit_pro_runner.helpers import read_only

        canonical_root = REPO_ROOT.resolve()
        missing_root = Path("/missing-prunable-worktree")
        output = (
            f"worktree {canonical_root}\0HEAD abc\0branch refs/heads/main\0\0"
            f"worktree {missing_root}\0HEAD def\0prunable gitdir file points to a missing location\0\0"
        )
        original_resolve = Path.resolve

        def guarded_resolve(path: Path, strict: bool = False) -> Path:
            if path == missing_root:
                raise AssertionError("prunable roots must not be canonicalized")
            return original_resolve(path, strict=strict)

        completed = SimpleNamespace(returncode=0, stdout=output, stderr="")
        with patch.object(read_only.subprocess, "run", return_value=completed), patch.object(
            Path, "resolve", guarded_resolve
        ):
            entries, error = read_only.registered_worktree_entries(canonical_root)

        self.assertEqual(entries, [(canonical_root, canonical_root)])
        self.assertIsNone(error)

    def test_registered_worktree_entries_fails_closed_on_unreadable_registered_entry(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        from speckit_pro_runner.helpers import read_only

        canonical_root = REPO_ROOT.resolve()
        denied_root = Path("/denied-registered-worktree")
        output = (
            f"worktree {canonical_root}\0HEAD abc\0branch refs/heads/main\0\0"
            f"worktree {denied_root}\0HEAD def\0branch refs/heads/feature\0\0"
        )
        original_resolve = Path.resolve

        def guarded_resolve(path: Path, strict: bool = False) -> Path:
            if path == denied_root:
                raise PermissionError("sandbox denied")
            return original_resolve(path, strict=strict)

        completed = SimpleNamespace(returncode=0, stdout=output, stderr="")
        with patch.object(read_only.subprocess, "run", return_value=completed), patch.object(
            Path, "resolve", guarded_resolve
        ):
            entries, error = read_only.registered_worktree_entries(canonical_root)

        self.assertEqual(entries, [])
        self.assertIn("registered worktree cannot be canonicalized", error or "")
        self.assertIn(denied_root.as_posix(), error or "")
        self.assertIn("sandbox denied", error or "")

    def test_resolve_workflow_binding_absolute_path_uses_longest_registered_root(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        with tempfile.TemporaryDirectory() as temp:
            task_root, descendant_root, _ = self.build_binding_worktrees(Path(temp))
            relative = Path("specs") / "workflow.md"
            (task_root / relative).parent.mkdir()
            (descendant_root / relative).parent.mkdir()
            (task_root / relative).write_text("# stale parent copy\n", encoding="utf-8")
            (descendant_root / relative).write_text("# nested owner\n", encoding="utf-8")

            payload, exit_code = self.binding_result(task_root, str(descendant_root / relative))
            self.assertEqual(
                (payload["binding_status"], payload["relation"], exit_code),
                ("resolved", "descendant", 0),
            )
            self.assertEqual(payload["workflow_root"], descendant_root.resolve().as_posix())
            self.assertEqual(payload["workflow_file"], (descendant_root / relative).resolve().as_posix())

            rebound, exit_code = self.binding_result(descendant_root, str(descendant_root / relative))
            self.assertEqual(
                (rebound["binding_status"], rebound["relation"], exit_code),
                ("resolved", "same", 0),
            )
            self.assertEqual(rebound["workflow_root"], descendant_root.resolve().as_posix())
            self.assertEqual(rebound["workflow_file"], (descendant_root / relative).resolve().as_posix())

    def test_resolve_workflow_binding_rejects_external_symlink_alias_into_worktree(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            task_root, descendant_root, _ = self.build_binding_worktrees(base)
            workflow = descendant_root / "aliased-workflow.md"
            workflow.write_text("# registered target\n", encoding="utf-8")
            alias = base / "workflow-link"
            try:
                alias.symlink_to(descendant_root, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            payload, exit_code = self.binding_result(task_root, str(alias / workflow.name))

            self.assertEqual((payload["binding_status"], exit_code), ("invalid", 1))
            self.assertIsNone(payload["relation"])
            self.assertEqual(payload["candidates"], [])
            self.assertIn("outside every registered worktree", payload["problems"][0])

    def test_resolve_workflow_binding_allows_in_worktree_symlink_with_same_owner(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            task_root, descendant_root, _ = self.build_binding_worktrees(base)
            target_dir = descendant_root / "workflow-target"
            target_dir.mkdir()
            workflow = target_dir / "workflow.md"
            workflow.write_text("# same owner\n", encoding="utf-8")
            alias = descendant_root / "workflow-link"
            try:
                alias.symlink_to(target_dir, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            payload, exit_code = self.binding_result(task_root, str(alias / workflow.name))

            self.assertEqual(
                (payload["binding_status"], payload["relation"], exit_code),
                ("resolved", "descendant", 0),
            )
            self.assertEqual(payload["workflow_root"], descendant_root.resolve().as_posix())
            self.assertEqual(payload["workflow_file"], workflow.resolve().as_posix())

    def test_resolve_workflow_binding_rejects_ambiguous_missing_and_unregistered_paths(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            task_root, descendant_root, _ = self.build_binding_worktrees(base)
            duplicate = Path("duplicate-workflow.md")
            (task_root / duplicate).write_text("# parent\n", encoding="utf-8")
            (descendant_root / duplicate).write_text("# nested\n", encoding="utf-8")

            payload, exit_code = self.binding_result(task_root, duplicate.as_posix())
            self.assertEqual((payload["binding_status"], exit_code), ("ambiguous", 1))
            self.assertEqual(
                payload["candidates"],
                [task_root.resolve().as_posix(), descendant_root.resolve().as_posix()],
            )

            payload, exit_code = self.binding_result(task_root, "missing-workflow.md")
            self.assertEqual((payload["binding_status"], exit_code), ("missing", 1))

            payload, exit_code = self.binding_result(task_root, str(descendant_root / "missing-absolute.md"))
            self.assertEqual((payload["binding_status"], exit_code), ("missing", 1))

            invalid_directory = descendant_root / "not-a-workflow.md"
            invalid_directory.mkdir()
            payload, exit_code = self.binding_result(task_root, invalid_directory.name)
            self.assertEqual((payload["binding_status"], exit_code), ("invalid", 1))

            unregistered = base / "unregistered" / "workflow.md"
            unregistered.parent.mkdir()
            unregistered.write_text("# unregistered\n", encoding="utf-8")
            payload, exit_code = self.binding_result(task_root, str(unregistered))
            self.assertEqual((payload["binding_status"], exit_code), ("invalid", 1))

    def test_resolve_workflow_binding_rejects_symlink_escape(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-workflow-binding":
            self.skipTest("workflow-binding cases use resolve-workflow-binding")
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            task_root, descendant_root, external_root = self.build_binding_worktrees(base)
            outside = base / "outside-workflow.md"
            outside.write_text("# outside\n", encoding="utf-8")
            parent = task_root / "parent-workflow.md"
            parent.write_text("# parent\n", encoding="utf-8")
            sibling = external_root / "sibling-workflow.md"
            sibling.write_text("# sibling\n", encoding="utf-8")
            links = [
                (descendant_root / "outside-escape-workflow.md", outside),
                (descendant_root / "parent-escape-workflow.md", parent),
                (descendant_root / "sibling-escape-workflow.md", sibling),
            ]
            try:
                for link, target in links:
                    link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            for link, _ in links:
                with self.subTest(link=link.name):
                    payload, exit_code = self.binding_result(task_root, str(link))
                    self.assertEqual((payload["binding_status"], exit_code), ("invalid", 1))
                    self.assertTrue(payload["problems"])

    def test_windows_style_relative_paths_are_normalized_before_execution(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("path-normalization case uses check-prerequisites")
        windows_workflow = WORKFLOW_FILE.replace("/", "\\")
        completed, response, stderr_records = run_runner(
            helper_request("check-prerequisites", {"workflow_file": windows_workflow})
        )
        self.assertIn(completed.returncode, {0, 1})
        self.assertIn(response["status"], {"ok", "expected_failure"})
        self.assertEqual(response["data"]["argv"][-2:], ["-m", "speckit_pro_runner"])
        workflow_checks = [
            check
            for check in response["data"]["stdout_json"]["checks"]
            if check["check"] == "workflow_file"
        ]
        self.assertEqual(workflow_checks[0]["detail"], WORKFLOW_FILE)
        self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])

    def test_explicit_repo_root_cannot_redefine_trust_boundary(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("repo_root trust-boundary case uses detect-commands")
        with tempfile.TemporaryDirectory() as outside:
            outside_root = Path(outside)
            (outside_root / "speckit-pro" / "speckit_pro_runner").mkdir(parents=True)
            completed, response, stderr_records = run_runner(
                helper_request("detect-commands", {"repo_root": str(outside_root)})
            )
        self.assertEqual(completed.returncode, 2)
        self.assert_response(response, "input_error", 2)
        self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["unsupported_path"])
        self.assertEqual([diag["code"] for diag in stderr_records], ["unsupported_path"])

    def test_repo_root_symlink_escape_is_rejected(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("repo_root symlink-boundary case uses detect-commands")
        with helper_project() as project_path, tempfile.TemporaryDirectory() as outside:
            outside_root = Path(outside)
            (outside_root / "speckit-pro" / "speckit_pro_runner").mkdir(parents=True)
            link = project_path / "external"
            try:
                link.symlink_to(outside_root, target_is_directory=True)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            completed, response, stderr_records = run_runner(
                helper_request("detect-commands", {"repo_root": link.relative_to(project_path).as_posix()}),
                cwd=project_path,
            )
        self.assertEqual(completed.returncode, 2)
        self.assert_response(response, "input_error", 2)
        self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["unsupported_path"])
        self.assertEqual([diag["code"] for diag in stderr_records], ["unsupported_path"])

    def test_find_repo_root_rejects_symlinked_plugin_anchor(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("repo-root discovery case uses check-prerequisites")
        with tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as outside:
            project_path = Path(project)
            outside_plugin = Path(outside) / "speckit-pro"
            (outside_plugin / "speckit_pro_runner").mkdir(parents=True)
            try:
                (project_path / "speckit-pro").symlink_to(outside_plugin, target_is_directory=True)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            from speckit_pro_runner.helpers.read_only import find_repo_root

            self.assertIsNone(find_repo_root(project_path))

    def test_find_repo_root_falls_back_to_specify_project_root(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("repo-root discovery case uses check-prerequisites")
        with tempfile.TemporaryDirectory() as project:
            project_path = Path(project)
            (project_path / ".specify").mkdir()
            nested = project_path / "docs" / "ai" / "specs"
            nested.mkdir(parents=True)
            from speckit_pro_runner.helpers.read_only import find_repo_root

            self.assertEqual(find_repo_root(nested), project_path.resolve())

    def test_find_repo_root_prefers_nearest_specify_anchor_over_ancestor_runner(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("repo-root discovery case uses check-prerequisites")
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "source"
            (source_root / "speckit-pro" / "speckit_pro_runner").mkdir(parents=True)
            worktree_root = source_root / ".worktrees" / "feature"
            (worktree_root / ".specify").mkdir(parents=True)

            from speckit_pro_runner.helpers.read_only import find_repo_root

            self.assertEqual(find_repo_root(worktree_root), worktree_root.resolve(strict=False))

    def test_find_repo_root_prefers_vendored_runner_over_specify_fallback(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("repo-root discovery case uses check-prerequisites")
        with tempfile.TemporaryDirectory() as project:
            project_path = Path(project)
            (project_path / ".specify").mkdir()
            vendored = project_path / "sub"
            (vendored / "speckit-pro" / "speckit_pro_runner").mkdir(parents=True)
            start = vendored / "deeper"
            start.mkdir()
            from speckit_pro_runner.helpers.read_only import find_repo_root

            self.assertEqual(find_repo_root(start), vendored.resolve())

    def test_find_repo_root_rejects_symlinked_specify_anchor(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("repo-root discovery case uses check-prerequisites")
        with tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as outside:
            project_path = Path(project)
            outside_specify = Path(outside) / ".specify"
            outside_specify.mkdir()
            try:
                (project_path / ".specify").symlink_to(outside_specify, target_is_directory=True)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            from speckit_pro_runner.helpers.read_only import find_repo_root

            self.assertIsNone(find_repo_root(project_path))

    def test_find_specify_returns_none_when_home_is_unresolvable(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("specify discovery case uses check-prerequisites")
        from speckit_pro_runner.helpers import read_only

        with patch.object(read_only.shutil, "which", return_value=None), patch.object(
            read_only.Path, "home", side_effect=RuntimeError("no home directory")
        ):
            self.assertIsNone(read_only.find_specify())

    def test_helper_argv_uses_runner_even_when_registered_script_is_symlinked(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("helper argv script-boundary case uses check-prerequisites")
        with helper_project() as project_path, tempfile.TemporaryDirectory() as outside:
            outside_script = Path(outside) / "helper.sh"
            outside_script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            try:
                (project_path / "helper.sh").symlink_to(outside_script)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            from speckit_pro_runner.helpers.read_only import helper_argv

            result = helper_argv(SimpleNamespace(helper_id="check-prerequisites", script="helper.sh"), {}, project_path)
            self.assertIsInstance(result, list)
            self.assertEqual(result[-2:], ["-m", "speckit_pro_runner"])

    def test_helper_result_reports_executable_runner_stdin_request(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("helper argv/stdin metadata case uses detect-commands")
        completed, response, stderr_records = run_runner(helper_request("detect-commands"))
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(stderr_records, [])
        self.assert_response(response, "ok", 0)
        data = response["data"]
        self.assertEqual(data["argv"][-2:], ["-m", "speckit_pro_runner"])
        self.assertEqual(data["argv_role"], "replay_runner_command")
        self.assertEqual(data["execution_model"], "direct_python_helper")
        self.assertTrue(data["executed_in_process"])
        self.assertEqual(data["stdin_mode"], "single_json_request")
        self.assertEqual(
            data["invocation_contract"],
            {
                "actual_execution_uses_argv": False,
                "argv_executable_without_stdin": False,
                "stdin_required": True,
                "stdin_request_field": "stdin_request",
            },
        )
        stdin_request = data["stdin_request"]
        self.assertEqual(stdin_request["helper_id"], "detect-commands")
        self.assertEqual(stdin_request["operation"], "detect-commands")
        replay_argv = data["argv"]
        self.assertIsInstance(replay_argv, list)
        self.assertEqual(replay_argv[0], sys.executable)
        replay = subprocess.run(
            [sys.executable, *replay_argv[1:]],
            input=json.dumps(stdin_request),
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
            env=runner_env(),
            shell=False,
            check=False,
        )
        self.assertEqual(replay.returncode, 0, replay.stderr)
        replay_response = json.loads(replay.stdout)
        self.assertEqual(replay_response["status"], "ok")

    def test_detect_commands_rejects_file_repo_root_and_reports_directory_cwd(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("detect-commands repo_root validation case")
        with helper_project() as root:
            project_path = root / "nested"
            project_path.mkdir()
            file_root = project_path / "not-a-directory"
            file_root.write_text("", encoding="utf-8")
            completed, response, stderr_records = run_runner(
                helper_request("detect-commands", {"repo_root": file_root.relative_to(root).as_posix()}), cwd=root
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["invalid_input"])
            self.assertEqual([diag["code"] for diag in stderr_records], ["invalid_input"])

            (project_path / "pnpm-lock.yaml").write_text("", encoding="utf-8")
            (project_path / "package.json").write_text('{"scripts":{"test":"vitest"}}\n', encoding="utf-8")
            completed, response, stderr_records = run_runner(
                helper_request("detect-commands", {"repo_root": project_path.relative_to(root).as_posix()}), cwd=root
            )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        self.assertEqual(response["data"]["cwd"]["value"], ".")
        self.assertEqual(response["data"]["effective_cwd"]["value"], project_path.relative_to(root).as_posix())
        self.assertEqual(stderr_records, [])

    def test_detect_commands_defaults_package_json_only_node_to_npm(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("detect-commands package-json-only case")
        with helper_project() as project_path:
            (project_path / "package.json").write_text('{"scripts":{"build":"vite","test":"vitest"}}\n', encoding="utf-8")
            completed, response, stderr_records = run_runner(
                helper_request("detect-commands", {"repo_root": "."}), cwd=project_path
            )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        stdout_json = response["data"]["stdout_json"]
        self.assertEqual(stdout_json["stack"], "nodejs")
        self.assertEqual(stdout_json["package_manager"], "npm")
        self.assertEqual(stdout_json["commands"]["BUILD"], "npm build")
        self.assertEqual(stdout_json["commands"]["UNIT_TEST"], "npm test")
        self.assertEqual(stderr_records, [])

    def test_detect_commands_reads_text_bun_lock_as_bun(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("detect-commands text bun.lock case")
        with helper_project() as project_path:
            # Bun 1.2 and later write the text bun.lock; bun.lockb is the legacy binary form.
            (project_path / "bun.lock").write_text("{}\n", encoding="utf-8")
            (project_path / "package.json").write_text(
                '{"scripts":{"build":"bun run scripts/build.ts","test":"bun run scripts/test.ts"}}\n', encoding="utf-8"
            )
            completed, response, stderr_records = run_runner(
                helper_request("detect-commands", {"repo_root": "."}), cwd=project_path
            )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        stdout_json = response["data"]["stdout_json"]
        self.assertEqual(stdout_json["package_manager"], "bun")
        # `bun test` and `bun build` are built-ins that would bypass these scripts.
        self.assertEqual(stdout_json["commands"]["UNIT_TEST"], "bun run test")
        self.assertEqual(stdout_json["commands"]["BUILD"], "bun run build")
        self.assertEqual(stdout_json["gates"]["COMPLEXITY"]["signal"], "bun.lock")
        self.assertEqual(stderr_records, [])

    def test_detect_commands_probes_symlinked_node_bins_inside_node_modules(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("detect-commands node_modules/.bin probe case")
        with helper_project() as project_path, tempfile.TemporaryDirectory() as outside:
            (project_path / "bun.lock").write_text("{}\n", encoding="utf-8")
            (project_path / "package.json").write_text('{"scripts":{"test":"bun test"}}\n', encoding="utf-8")
            bin_dir = project_path / "node_modules" / ".bin"
            bin_dir.mkdir(parents=True)
            # Package managers install .bin entries as symlinks into node_modules.
            package_bin = project_path / "node_modules" / "oxlint" / "bin" / "oxlint"
            package_bin.parent.mkdir(parents=True)
            package_bin.write_text("#!/bin/sh\n", encoding="utf-8")
            (bin_dir / "oxlint").symlink_to(Path("..") / "oxlint" / "bin" / "oxlint")
            # A link that escapes the project's node_modules never counts as installed.
            escaped = Path(outside) / "stryker"
            escaped.write_text("#!/bin/sh\n", encoding="utf-8")
            (bin_dir / "stryker").symlink_to(escaped)
            completed, response, _ = run_runner(
                helper_request("detect-commands", {"repo_root": "."}), cwd=project_path
            )
        self.assertEqual(completed.returncode, 0)
        gates = response["data"]["stdout_json"]["gates"]
        self.assertIs(gates["COMPLEXITY"]["tool_present"], True)
        self.assertIs(gates["MUTATION"]["tool_present"], False)

    def test_detect_commands_subdir_matches_bash_reference_from_effective_cwd(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("detect-commands effective-cwd parity case")
        with helper_project() as root:
            project_path = root / "nested"
            project_path.mkdir()
            (project_path / "package-lock.json").write_text("{}\n", encoding="utf-8")
            (project_path / "package.json").write_text(
                '{"scripts":{"build":"vite","typecheck":"tsc --noEmit","lint":"eslint .","test":"vitest","test:e2e":"playwright test"}}\n',
                encoding="utf-8",
            )
            response = self.assert_helper_matches_bash_reference(
                "detect-commands",
                {"repo_root": project_path.relative_to(root).as_posix()},
                cwd=root,
            )
        self.assertEqual(response["data"]["cwd"]["value"], ".")
        self.assertNotEqual(response["data"]["effective_cwd"]["value"], ".")

    def test_redundant_confidence_gate_path_is_canonicalized_before_execution(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate canonical argv case")
        redundant_workflow = "tests/speckit-pro/unit/fixtures/autopilot-stage/../autopilot-stage/workflow.md"
        response = self.assert_helper_matches_bash_reference(
            "confidence-gate",
            {"workflow_file": redundant_workflow, "mode_name": "advisory"},
        )
        self.assertEqual(response["data"]["argv"][-2:], ["-m", "speckit_pro_runner"])
        self.assertNotIn("..", response["data"]["stdout"]["text"])

    def test_check_prerequisites_uses_canonical_input_for_replay(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("check-prerequisites canonical argv case")
        redundant_workflow = "tests/speckit-pro/unit/fixtures/autopilot-stage/../autopilot-stage/workflow.md"
        response = self.assert_helper_matches_bash_reference(
            "check-prerequisites",
            {"workflow_file": redundant_workflow},
        )
        workflow_checks = [
            check
            for check in response["data"]["stdout_json"]["checks"]
            if check["check"] == "workflow_file"
        ]
        self.assertEqual(workflow_checks[0]["detail"], WORKFLOW_FILE)

    def test_confidence_gate_rejects_invalid_threshold(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate threshold case")
        cases = [
            {"workflow_file": WORKFLOW_FILE, "threshold": "abc"},
            {"workflow_file": WORKFLOW_FILE, "threshold": "nan"},
            {"workflow_file": WORKFLOW_FILE, "mode_name": "maybe"},
        ]
        for inputs in cases:
            with self.subTest(inputs=inputs):
                completed, response, stderr_records = run_runner(helper_request("confidence-gate", inputs))
                self.assertEqual(completed.returncode, 2)
                self.assert_response(response, "input_error", 2)
                self.assertTrue("invalid threshold" in response["data"]["stdout_json"]["error"] or "invalid mode" in response["data"]["stdout_json"]["error"])
                self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])

    def test_confidence_gate_runner_classifies_domain_verdicts(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate runner verdict case")
        with tempfile.TemporaryDirectory(prefix="confidence-runner-", dir=REPO_ROOT) as directory:
            workflow = Path(directory) / "workflow.md"
            relative = workflow.relative_to(REPO_ROOT).as_posix()
            cases = (
                ("0.90", "advisory", "ok", 0, "proceed"),
                ("0.80", "advisory", "ok", 2, "continue_with_warning"),
                ("0.80", "strict", "expected_failure", 2, "stop"),
                (None, "advisory", "ok", 1, "soft_skip"),
            )
            for score, mode, status, exit_code, action in cases:
                with self.subTest(score=score, mode=mode):
                    criteria = (score,) * 5 if score is not None else None
                    workflow.write_text(self.confidence_emit(score, criteria), encoding="utf-8")
                    completed, response, _ = run_runner(helper_request("confidence-gate", {
                        "workflow_file": relative, "mode_name": mode, "threshold": "0.90",
                    }))
                    self.assertEqual(response["status"], status, response)
                    self.assertEqual(response["data"]["exit_code"], exit_code)
                    self.assertEqual(response["data"]["stdout_json"]["recommended_action"], action)
                    self.assertEqual(completed.returncode, 0 if status == "ok" else 1)
            workflow.unlink()
            _, response, _ = run_runner(helper_request("confidence-gate", {"workflow_file": relative}))
            self.assertNotEqual(response["status"], "ok")
            quoted_path = f'{relative}"'
            _, response, _ = run_runner(helper_request("confidence-gate", {"workflow_file": quoted_path}))
            self.assertEqual(response["status"], "missing_prerequisite", response)
            self.assertEqual(
                response["diagnostics"][0]["message"],
                f"workflow file not found: {quoted_path}",
            )
            self.assertIn(relative, str(response["diagnostics"]))

    def test_confidence_gate_error_shape_is_not_promoted(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate error shape case")
        from speckit_pro_runner.helpers.read_only import confidence_verdict_status

        self.assertIsNone(confidence_verdict_status({"error": "invalid threshold"}, 2))
        self.assertIsNone(confidence_verdict_status({"pass": False, "recommended_action": "continue_with_warning"}, 2))
        verdict = self.run_confidence_gate(self.confidence_emit("0.80", ("0.80",) * 5))["json"]
        verdict["mode"] = []
        self.assertIsNone(confidence_verdict_status(verdict, 2))

    def write_confidence_workflow(self, directory: str, body: str) -> str:
        workflow = Path(directory) / "confidence-workflow.md"
        workflow.write_text(body, encoding="utf-8")
        return workflow.name

    def run_confidence_gate(self, body: str, **inputs: object) -> dict[str, object]:
        from speckit_pro_runner.helpers.read_only import confidence_gate

        with tempfile.TemporaryDirectory(prefix="confidence-workflow-") as directory:
            request = {"workflow_file": self.write_confidence_workflow(directory, body), "mode_name": "advisory"}
            request.update(inputs)
            result = confidence_gate(request, Path(directory).resolve())
        return {"exit_code": result["exit_code"], "stderr": result["stderr"], "json": json.loads(result["stdout"])}

    def test_confidence_workflow_is_isolated_and_cleaned_after_failure(self) -> None:
        from speckit_pro_runner.helpers.read_only import confidence_gate

        roots: list[Path] = []

        def inspect_fixture(request: dict[str, object], root: Path) -> dict[str, object]:
            roots.append(root)
            self.assertFalse(root.resolve().is_relative_to(REPO_ROOT.resolve()))
            self.assertEqual((root / str(request["workflow_file"])).read_text(encoding="utf-8"), "# Workflow\n")
            if len(roots) == 2:
                raise RuntimeError("fixture cleanup probe")
            return confidence_gate(request, root)

        with patch("speckit_pro_runner.helpers.read_only.confidence_gate", side_effect=inspect_fixture):
            self.run_confidence_gate("# Workflow\n")
            with self.assertRaisesRegex(RuntimeError, "fixture cleanup probe"):
                self.run_confidence_gate("# Workflow\n")
        self.assertEqual(len(roots), 2)
        self.assertTrue(all(not root.exists() for root in roots))

    ANALYSIS_HEADER = ("| ID | Severity | Issue | Resolution |", "|----|----------|-------|------------|")

    SEVERITY_LEGEND = "\n".join(
        (
            "| Severity | Meaning | Action Required |",
            "|----------|---------|-----------------|",
            "| `CRITICAL` | Blocks implementation, violates constitution | **Must fix before G6 gate** |",
            "| `HIGH` | Significant gap, impacts quality | Should fix |",
            "| `MEDIUM` | Improvement opportunity | Review and decide |",
            "| `LOW` | Minor inconsistency | Note for future |",
        )
    )

    @classmethod
    def analysis_table(cls, rows: tuple[tuple[str, str, str, str], ...]) -> str:
        lines = list(cls.ANALYSIS_HEADER)
        lines.extend("| " + " | ".join(row) + " |" for row in rows)
        return "\n".join(lines)

    @classmethod
    def confidence_emit(
        cls,
        stated: str | None,
        criteria: tuple[str, str, str, str, str] | None,
        prose: str = "",
        analysis_rows: tuple[tuple[str, str, str, str], ...] | None = None,
    ) -> str:
        lines = ["# Workflow", "", "## Phase 6: Analyze", ""]
        if prose:
            lines.extend([prose, ""])
        if analysis_rows is not None:
            lines.extend(["### Analysis Results", "", cls.analysis_table(analysis_rows), ""])
        if stated is not None:
            lines.extend([f"📊 Confidence: {stated}", ""])
        if criteria is not None:
            labels = ("Task understanding", "Approach clarity", "Requirements alignment", "Risk assessment", "Completeness")
            lines.extend(f"- {label}: {score}" for label, score in zip(labels, criteria, strict=True))
        return "\n".join(lines) + "\n"

    def test_confidence_gate_computes_composite_from_criterion_mean(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate composite case")
        outcome = self.run_confidence_gate(self.confidence_emit("0.99", ("0.95", "0.85", "0.95", "0.90", "0.85")))
        payload = outcome["json"]
        self.assertEqual(payload["composite"], 0.90)
        self.assertEqual(payload["composite_source"], "computed")
        self.assertEqual(payload["criteria_mean"], 0.90)
        self.assertEqual(payload["deductions"], {"critical": 0, "high": 0, "amount": 0.0})
        self.assertFalse(payload["deductions_applied"])
        self.assertTrue(payload["pass"])
        self.assertEqual(outcome["exit_code"], 0)

    def test_confidence_gate_rounds_the_criterion_mean_to_two_decimals(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate rounding case")
        outcome = self.run_confidence_gate(self.confidence_emit(None, ("0.95", "0.80", "0.90", "0.75", "0.86")))
        self.assertEqual(outcome["json"]["criteria_mean"], 0.85)
        self.assertEqual(outcome["json"]["composite"], 0.85)
        self.assertEqual(outcome["json"]["composite_source"], "computed")

    def test_confidence_gate_deducts_for_unresolved_analysis_rows(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate deduction case")
        cases = (
            ((("A1", "CRITICAL", "contract undefined", ""),), 1, 0, 0.30, 0.70),
            ((("A1", "HIGH", "cookie policy unspecified", ""),), 0, 1, 0.10, 0.90),
            (
                (("A1", "CRITICAL", "contract undefined", ""), ("A2", "HIGH", "cookie policy unspecified", "")),
                1,
                1,
                0.40,
                0.60,
            ),
        )
        for rows, critical, high, amount, composite in cases:
            with self.subTest(rows=rows):
                outcome = self.run_confidence_gate(
                    self.confidence_emit(None, ("1.00", "1.00", "1.00", "1.00", "1.00"), analysis_rows=rows)
                )
                payload = outcome["json"]
                self.assertEqual(payload["criteria_mean"], 1.00)
                self.assertEqual(payload["deductions"], {"critical": critical, "high": high, "amount": amount})
                self.assertTrue(payload["deductions_applied"])
                self.assertEqual(payload["composite"], composite)

    def test_confidence_gate_stops_deducting_once_the_resolution_cell_is_filled(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate remediation case")
        rows = (
            ("A1", "CRITICAL", "contract undefined", "Contract added to `contracts/api.md`."),
            ("A2", "HIGH", "cookie policy unspecified", "Policy stated in `plan.md`."),
        )
        outcome = self.run_confidence_gate(
            self.confidence_emit(None, ("1.00", "1.00", "1.00", "1.00", "1.00"), analysis_rows=rows)
        )
        payload = outcome["json"]
        self.assertEqual(payload["deductions"], {"critical": 0, "high": 0, "amount": 0.0})
        self.assertFalse(payload["deductions_applied"])
        self.assertEqual(payload["composite"], 1.00)
        self.assertTrue(payload["pass"])
        self.assertEqual(outcome["exit_code"], 0)

    def test_confidence_gate_ignores_unresolved_medium_and_low_rows(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate severity scope case")
        rows = (("A1", "MEDIUM", "naming inconsistency", ""), ("A2", "LOW", "typo in heading", ""))
        outcome = self.run_confidence_gate(
            self.confidence_emit(None, ("1.00", "1.00", "1.00", "1.00", "1.00"), analysis_rows=rows)
        )
        payload = outcome["json"]
        self.assertEqual(payload["deductions"], {"critical": 0, "high": 0, "amount": 0.0})
        self.assertEqual(payload["composite"], 1.00)

    def test_confidence_gate_ignores_bracket_severity_prose_in_the_log(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate bracket prose case")
        clean_scan = (
            "| Marker scan | Clean | New Plan artifacts contain 0 `[NEEDS CLARIFICATION]`, 0 `[Gap]`, "
            "0 `[CRITICAL]`, and 0 `[HIGH]` markers |"
        )
        remediated = "- F1 [HIGH]: Packet-validation fallback wording could be read as allowing a fallback."
        for prose in (clean_scan, remediated, clean_scan + "\n" + remediated):
            with self.subTest(prose=prose):
                outcome = self.run_confidence_gate(
                    self.confidence_emit(None, ("1.00", "1.00", "1.00", "1.00", "1.00"), prose=prose)
                )
                payload = outcome["json"]
                self.assertEqual(payload["deductions"], {"critical": 0, "high": 0, "amount": 0.0})
                self.assertFalse(payload["deductions_applied"])
                self.assertEqual(payload["composite"], 1.00)
                self.assertTrue(payload["pass"])
                self.assertEqual(outcome["exit_code"], 0)

    def test_confidence_gate_ignores_the_severity_legend_table(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate legend table case")
        outcome = self.run_confidence_gate(
            self.confidence_emit(None, ("1.00", "1.00", "1.00", "1.00", "1.00"), prose=self.SEVERITY_LEGEND)
        )
        payload = outcome["json"]
        self.assertEqual(payload["deductions"], {"critical": 0, "high": 0, "amount": 0.0})
        self.assertEqual(payload["composite"], 1.00)
        self.assertEqual(outcome["exit_code"], 0)

    def test_confidence_gate_reads_only_the_most_recent_analysis_table(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate latest table case")
        earlier = self.analysis_table((("A1", "CRITICAL", "contract undefined", ""),))
        body = self.confidence_emit(
            None,
            ("1.00", "1.00", "1.00", "1.00", "1.00"),
            prose="### Analysis Results (pass 1)\n\n" + earlier,
            analysis_rows=(("A1", "CRITICAL", "contract undefined", "Contract added to `contracts/api.md`."),),
        )
        outcome = self.run_confidence_gate(body)
        payload = outcome["json"]
        self.assertEqual(payload["deductions"], {"critical": 0, "high": 0, "amount": 0.0})
        self.assertEqual(payload["composite"], 1.00)

    def test_confidence_gate_floors_the_composite_at_zero(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate floor case")
        rows = tuple((f"A{index}", "CRITICAL", "unresolved", "") for index in range(1, 5))
        outcome = self.run_confidence_gate(
            self.confidence_emit("0.95", ("0.20", "0.20", "0.20", "0.20", "0.20"), analysis_rows=rows)
        )
        payload = outcome["json"]
        self.assertEqual(payload["deductions"]["amount"], 1.20)
        self.assertEqual(payload["composite"], 0.00)
        self.assertFalse(payload["pass"])
        self.assertEqual(outcome["exit_code"], 2)

    def test_confidence_gate_falls_back_to_the_stated_line_without_criteria(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate fallback case")
        outcome = self.run_confidence_gate(
            self.confidence_emit("0.92", None, analysis_rows=(("A1", "CRITICAL", "ignored", ""),))
        )
        payload = outcome["json"]
        self.assertEqual(payload["composite"], 0.92)
        self.assertEqual(payload["composite_source"], "stated")
        self.assertIsNone(payload["criteria_mean"])
        self.assertFalse(payload["deductions_applied"])
        self.assertEqual(payload["deductions"], {"critical": 0, "high": 0, "amount": 0.0})
        self.assertTrue(payload["pass"])

    def test_confidence_gate_reads_a_deduction_as_agreement_not_mismatch(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate deduction agreement case")
        outcome = self.run_confidence_gate(
            self.confidence_emit(
                "0.95",
                ("0.95", "0.95", "0.95", "0.95", "0.95"),
                analysis_rows=(("A1", "HIGH", "open finding", ""),),
            )
        )
        payload = outcome["json"]
        self.assertEqual(payload["criteria_mean"], 0.95)
        self.assertEqual(payload["composite"], 0.85)
        self.assertNotIn("stated", payload["reason"])

    def test_confidence_gate_surfaces_a_stated_versus_computed_mismatch(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate mismatch case")
        outcome = self.run_confidence_gate(self.confidence_emit("0.95", ("0.80", "0.80", "0.80", "0.80", "0.80")))
        payload = outcome["json"]
        self.assertEqual(payload["composite"], 0.80)
        self.assertIn("stated 0.95", payload["reason"])
        self.assertIn("criterion mean 0.80", payload["reason"])
        agreeing = self.run_confidence_gate(self.confidence_emit("0.80", ("0.80", "0.80", "0.80", "0.80", "0.80")))
        self.assertNotIn("stated", agreeing["json"]["reason"])

    def test_confidence_gate_reports_no_data_without_either_source(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate no-data case")
        outcome = self.run_confidence_gate(self.confidence_emit(None, None))
        self.assertEqual(outcome["exit_code"], 1)
        self.assertIsNone(outcome["json"]["pass"])
        self.assertIn("NO_DATA", outcome["stderr"])

    def test_confidence_gate_runbooks_route_exit_two_through_deductions_applied(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate runbook parity case")
        for runbook in CONFIDENCE_GATE_RUNBOOKS:
            with self.subTest(runbook=runbook.name):
                self.assertIn(
                    "deductions_applied",
                    runbook.read_text(encoding="utf-8"),
                    f"{runbook.name} documents the exit-2 loop without naming the field it reads first",
                )
                self.assertIn("data.exit_code", runbook.read_text(encoding="utf-8"))
                self.assertIn("recommended_action", runbook.read_text(encoding="utf-8"))

    def test_confidence_gate_runbooks_do_not_route_remediation_by_risk_assessment(self) -> None:
        if self.helper_filter and self.helper_filter != "confidence-gate":
            self.skipTest("confidence-gate runbook routing case")
        # The synthesizer no longer deducts for open findings under Risk
        # assessment, so that criterion can never come back lowest because of
        # them. A runbook that still routes remediation through it sends the
        # operator down a branch that cannot fire.
        routing = re.compile(r"risk_assessment\"?\s*(?:lowest\s*)?(?:→|->)")
        for runbook in CONFIDENCE_GATE_RUNBOOKS:
            with self.subTest(runbook=runbook.name):
                collapsed = " ".join(runbook.read_text(encoding="utf-8").split())
                self.assertIsNone(
                    routing.search(collapsed),
                    f"{runbook.name} still routes confidence remediation by the risk_assessment criterion",
                )

    def test_generate_spec_index_ignores_symlinked_spec_children(self) -> None:
        if self.helper_filter and self.helper_filter != "generate-spec-index-check":
            self.skipTest("generate-spec-index path-boundary case")
        with helper_project() as root, tempfile.TemporaryDirectory() as outside:
            specs = root / "specs"
            specs.mkdir()
            outside_spec = Path(outside) / "escaped"
            outside_spec.mkdir()
            (outside_spec / "SPEC-MOC.md").write_text("---\nstatus: complete\n---\n", encoding="utf-8")
            try:
                (specs / "escaped").symlink_to(outside_spec, target_is_directory=True)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            completed, response, stderr_records = run_runner(
                helper_request("generate-spec-index-check", {"repo_root": "."}), cwd=root
            )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        self.assertIn("all in-scope maps up to date", response["data"]["stdout"]["text"])
        self.assertEqual(stderr_records, [])

    def test_o5_topology_reports_bad_child_shapes_without_crashing(self) -> None:
        if self.helper_filter and self.helper_filter != "o5-topology":
            self.skipTest("o5-topology shape case")
        with helper_project() as project:
            manifest = project / "o5-parent-manifest.json"
            manifest.write_text(
                json.dumps({"schemaVersion": 1, "kind": "o5_parent_manifest", "parent": {}, "children": ["bad", {"id": "c", "path": "specs/c", "dependsOn": "bad"}]}),
                encoding="utf-8",
            )
            completed, response, stderr_records = run_runner(
                helper_request("o5-topology", {"target": manifest.name}), cwd=project
            )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        codes = {problem["code"] for problem in response["data"]["stdout_json"]["problems"]}
        self.assertIn("invalid_child_shape", codes)
        self.assertIn("invalid_depends_on", codes)
        self.assertEqual(stderr_records, [])

    def test_validate_pr_packet_rejects_non_object_and_bad_nested_shapes(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet shape case")
        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            packet = Path(project) / "packet.json"
            packet.write_text('{"broken":\n', encoding="utf-8")
            completed, response, stderr_records = self.run_packet_runner(
                helper_request("validate-pr-packet-read-only", {"packet_path": packet.relative_to(self.packet_root).as_posix()})
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual(response["data"]["stdout_json"]["failures"][0]["rule"], "input.error")
            self.assertEqual(stderr_records, response["diagnostics"])

            packet.write_bytes(b'{"schema_version":"1.0.0","packet_id":"bad-\xff"}\n')
            completed, response, stderr_records = self.run_packet_runner(
                helper_request("validate-pr-packet-read-only", {"packet_path": packet.relative_to(self.packet_root).as_posix()})
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual(response["data"]["stdout_json"]["failures"][0]["rule"], "input.utf8")
            self.assertEqual(stderr_records, response["diagnostics"])

            packet.write_text("[]\n", encoding="utf-8")
            completed, response, stderr_records = self.run_packet_runner(
                helper_request("validate-pr-packet-read-only", {"packet_path": packet.relative_to(self.packet_root).as_posix()})
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])

            packet.write_text(
                json.dumps({"verification_evidence": ["ok"], "scope_evidence": [], "generated_title": [], "target": [], "validation_result_path": "../outside.json", "body_file": []}),
                encoding="utf-8",
            )
            completed, response, stderr_records = self.run_packet_runner(
                helper_request("validate-pr-packet-read-only", {"packet_path": packet.relative_to(self.packet_root).as_posix()})
            )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        rules = {failure["rule"] for failure in response["data"]["stdout_json"]["failures"]}
        self.assertIn("input.shape.scope_evidence", rules)
        self.assertIn("input.path.validation_result_path", rules)
        self.assertIn("input.path.body_file", rules)
        self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])

    def test_validate_pr_packet_reports_oversized_json_integer_as_input_error(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet oversized integer case")
        max_digits = getattr(sys, "get_int_max_str_digits", lambda: 0)()
        if max_digits <= 0:
            self.skipTest("Python JSON integer digit limit is disabled")
        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            packet = Path(project) / "packet.json"
            packet.write_text(
                '{"packet_id": "oversized-integer", "oversized": '
                + ("9" * (max_digits + 1))
                + "}\n",
                encoding="utf-8",
            )
            completed, response, stderr_records = self.run_packet_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    {"packet_path": packet.relative_to(self.packet_root).as_posix()},
                )
            )

        self.assertEqual(completed.returncode, 2)
        self.assert_response(response, "input_error", 2)
        self.assertEqual(response["data"]["stdout_json"]["failures"][0]["rule"], "input.error")
        self.assertNotIn("Traceback", completed.stderr)
        self.assertEqual(stderr_records, response["diagnostics"])

    def test_validate_pr_packet_rejects_schema_minimal_false_pass(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet schema case")
        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            packet = Path(project) / "minimal-packet.json"
            packet.write_text(
                json.dumps(
                    {
                        "verification_evidence": ["present"],
                        "scope_evidence": {"changed_files": ["README.md"]},
                        "validation_result_path": (
                            "specs/example/.process/pr-packets/minimal-packet/validation.json"
                        ),
                    }
                ),
                encoding="utf-8",
            )
            completed, response, stderr_records = self.run_packet_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    {"packet_path": packet.relative_to(self.packet_root).as_posix()},
                )
            )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        failures = response["data"]["stdout_json"]["failures"]
        self.assertIn("packet.schema.required", {failure["rule"] for failure in failures})
        missing_fields = {failure["field"] for failure in failures}
        self.assertTrue({"target", "generated_title", "body_file"}.issubset(missing_fields))
        self.assertEqual(stderr_records, response["diagnostics"])

    def test_validate_pr_packet_enforces_validation_result_source_fingerprint_schema(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet schema source fingerprint case")
        valid_packet_path = self.packet_fixture_dir / "valid-single.json"
        completed, response, _stderr_records = self.run_packet_runner(
            helper_request(
                "validate-pr-packet-read-only",
                {"packet_path": valid_packet_path.relative_to(self.packet_root).as_posix()},
            )
        )
        self.assertEqual(completed.returncode, 0)
        validation_result = response["data"]["stdout_json"]
        valid_packet = json.loads(valid_packet_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            packet = Path(project) / "source-fingerprints.json"
            for name, source_fingerprints, expected_rule in (
                ("empty", {}, "packet.schema.min_properties"),
                ("malformed", {"packet": {"path": "source-fingerprints.json"}}, "packet.schema.required"),
            ):
                with self.subTest(name=name):
                    packet.write_text(
                        json.dumps(
                            {
                                **valid_packet,
                                "packet_id": "source-fingerprints",
                                "validation_result_path": (
                                    "specs/fixture-pr-packet/.process/"
                                    "pr-packets/source-fingerprints/validation.json"
                                ),
                                "validation_result": {
                                    **validation_result,
                                    "source_fingerprints": source_fingerprints,
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    completed, response, stderr_records = self.run_packet_runner(
                        helper_request(
                            "validate-pr-packet-read-only",
                            {"packet_path": packet.relative_to(self.packet_root).as_posix()},
                        )
                    )
                    self.assertEqual(completed.returncode, 1)
                    self.assert_response(response, "expected_failure", 1)
                    rules = {failure["rule"] for failure in response["data"]["stdout_json"]["failures"]}
                    self.assertIn(expected_rule, rules)
                    self.assertEqual(stderr_records, response["diagnostics"])

    def test_validate_pr_packet_rejects_unsafe_missing_and_unreadable_body(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet body path case")
        valid_packet = json.loads((self.packet_fixture_dir / "valid-single.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            project_path = Path(project)
            packet = project_path / "packet.json"
            cases = {
                "unsafe": ("../outside.md", "input.path.body_file"),
                "missing": (
                    (project_path / "missing.md").relative_to(self.packet_root).as_posix(),
                    "body.path",
                ),
            }
            for name, (body_file, expected_rule) in cases.items():
                with self.subTest(name=name):
                    packet.write_text(
                        json.dumps({**valid_packet, "body_file": body_file}),
                        encoding="utf-8",
                    )
                    completed, response, stderr_records = self.run_packet_runner(
                        helper_request(
                            "validate-pr-packet-read-only",
                            {"packet_path": packet.relative_to(self.packet_root).as_posix()},
                        )
                    )
                    self.assertEqual(completed.returncode, 1)
                    self.assert_response(response, "expected_failure", 1)
                    rules = {
                        failure["rule"]
                        for failure in response["data"]["stdout_json"]["failures"]
                    }
                    self.assertIn(expected_rule, rules)
                    self.assertEqual(stderr_records, response["diagnostics"])

            body = project_path / "unreadable.md"
            body.write_text(
                (self.packet_fixture_dir / "bodies" / "valid-single.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            packet.write_text(
                json.dumps(
                    {
                        **valid_packet,
                        "body_file": body.relative_to(self.packet_root).as_posix(),
                    }
                ),
                encoding="utf-8",
            )
            from speckit_pro_runner.helpers import read_only

            original_trusted_bytes = read_only.trusted_bytes

            def unreadable_body(path: Path, root: Path | None = None) -> bytes | None:
                if path.resolve(strict=False) == body.resolve(strict=False):
                    return None
                return original_trusted_bytes(path, root)

            with patch.object(read_only, "trusted_bytes", side_effect=unreadable_body):
                result = read_only.validate_pr_packet_read_only(
                    {"packet_path": packet.relative_to(self.packet_root).as_posix()},
                    self.packet_root,
                )
        self.assertEqual(result["exit_code"], 1)
        failures = json.loads(result["stdout"])["failures"]
        self.assertIn("body.readable", {failure["rule"] for failure in failures})

        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            project_path = Path(project)
            body = project_path / "invalid-utf8.md"
            body.write_bytes((self.packet_fixture_dir / "bodies" / "valid-single.md").read_bytes() + b"\xff")
            packet = project_path / "invalid-body-utf8.json"
            packet.write_text(
                json.dumps(
                    {
                        **valid_packet,
                        "packet_id": "invalid-body-utf8",
                        "body_file": body.relative_to(self.packet_root).as_posix(),
                        "validation_result_path": (
                            "specs/fixture-pr-packet/.process/"
                            "pr-packets/invalid-body-utf8/validation.json"
                        ),
                    }
                ),
                encoding="utf-8",
            )
            completed, response, stderr_records = self.run_packet_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    {"packet_path": packet.relative_to(self.packet_root).as_posix()},
                )
            )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        failures = response["data"]["stdout_json"]["failures"]
        self.assertIn("body.utf8", {failure["rule"] for failure in failures})
        self.assertEqual(stderr_records, response["diagnostics"])

    def test_validate_pr_packet_rejects_validation_result_path_not_owned_by_packet(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet validation ownership case")
        valid_packet = json.loads((self.packet_fixture_dir / "valid-single.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            packet = Path(project) / "valid-single.json"
            packet.write_text(
                json.dumps(
                    {
                        **valid_packet,
                        "validation_result_path": "specs/other-feature/.process/pr-packets/valid-single/validation.json",
                    }
                ),
                encoding="utf-8",
            )
            completed, response, stderr_records = self.run_packet_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    {"packet_path": packet.relative_to(self.packet_root).as_posix()},
                )
            )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        rules = {failure["rule"] for failure in response["data"]["stdout_json"]["failures"]}
        self.assertIn("input.identity.validation_result_path", rules)
        self.assertEqual(stderr_records, response["diagnostics"])

    def test_validate_pr_packet_enforces_canonical_packet_owned_paths(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet canonical ownership case")
        valid_packet = json.loads((self.packet_fixture_dir / "valid-single.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="packet-identity-") as project:
            repo_root = Path(project)
            subprocess.run(
                ["git", "init", "--quiet", str(repo_root)],
                text=True,
                capture_output=True,
                shell=False,
                check=True,
            )
            (repo_root / ".specify").mkdir()
            feature_dir = repo_root / "specs" / "fixture-feature"
            source_feature_dir = feature_dir.relative_to(repo_root).as_posix()
            packet_id = "valid-single"
            packet_root = feature_dir / ".process" / "pr-packets"
            body_path = packet_root / packet_id / "body.md"
            body_path.parent.mkdir(parents=True)
            body_path.write_text(
                (self.packet_fixture_dir / "bodies" / "valid-single.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            packet_path = packet_root / f"{packet_id}.json"
            canonical_packet = {
                **valid_packet,
                "packet_id": packet_id,
                "source_feature_dir": source_feature_dir,
                "body_file": body_path.relative_to(repo_root).as_posix(),
                "validation_result_path": f"{source_feature_dir}/.process/pr-packets/{packet_id}/validation.json",
            }
            packet_path.write_text(json.dumps(canonical_packet), encoding="utf-8")
            completed, response, stderr_records = self.run_packet_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    {"packet_path": packet_path.relative_to(repo_root).as_posix()},
                ),
                cwd=repo_root,
            )
            self.assertEqual(completed.returncode, 0, response)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])

            cases = {
                "source_mismatch": (
                    {"source_feature_dir": "specs/other-feature"},
                    "input.identity.source_feature_dir",
                ),
                "body_mismatch": (
                    {"body_file": "fixtures/body.md"},
                    "input.identity.body_file",
                ),
                "validation_mismatch": (
                    {"validation_result_path": f"{source_feature_dir}/.process/pr-packets/other/validation.json"},
                    "input.identity.validation_result_path",
                ),
            }
            for name, (overrides, expected_rule) in cases.items():
                with self.subTest(name=name):
                    packet_path.write_text(
                        json.dumps({**canonical_packet, **overrides}),
                        encoding="utf-8",
                    )
                    completed, response, stderr_records = self.run_packet_runner(
                        helper_request(
                            "validate-pr-packet-read-only",
                            {"packet_path": packet_path.relative_to(repo_root).as_posix()},
                        ),
                        cwd=repo_root,
                    )
                    self.assertEqual(completed.returncode, 1)
                    self.assert_response(response, "expected_failure", 1)
                    rules = {
                        failure["rule"]
                        for failure in response["data"]["stdout_json"]["failures"]
                    }
                    self.assertIn(expected_rule, rules)
                    self.assertEqual(stderr_records, response["diagnostics"])

    def test_validate_pr_packet_checks_body_currentness_without_writing_state(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet currentness case")
        for packet_name in ("valid-single.json", "valid-split.json"):
            with self.subTest(packet_name=packet_name):
                valid_packet_path = self.packet_fixture_dir / packet_name
                completed, response, stderr_records = self.run_packet_runner(
                    helper_request(
                        "validate-pr-packet-read-only",
                        {"packet_path": valid_packet_path.relative_to(self.packet_root).as_posix()},
                    )
                )
                self.assertEqual(completed.returncode, 0)
                self.assert_response(response, "ok", 0)
                self.assertEqual(response["data"]["stdout_json"]["status"], "passed")
                self.assertEqual(set(response["data"]["stdout_json"]["source_fingerprints"]), {"body", "packet"})
                self.assertFalse(response["data"]["writes_state"])
                self.assertEqual(response["data"]["promotion_status"], "python_authoritative")
                self.assertEqual(stderr_records, [])

        stale_packet = self.packet_fixture_dir / "invalid-protected-edit.json"
        completed, response, stderr_records = self.run_packet_runner(
            helper_request(
                "validate-pr-packet-read-only",
                {"packet_path": stale_packet.relative_to(self.packet_root).as_posix()},
            )
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        stale_rules = {
            failure["rule"] for failure in response["data"]["stdout_json"]["failures"]
        }
        self.assertIn("body.protected_fingerprint", stale_rules)
        self.assertFalse(response["data"]["writes_state"])
        self.assertEqual(response["data"]["promotion_status"], "python_authoritative")
        self.assertEqual(stderr_records, response["diagnostics"])

        valid_packet = json.loads((self.packet_fixture_dir / "valid-single.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            packet = Path(project) / "current-editable-packet.json"
            packet.write_text(
                json.dumps(
                    {
                        **valid_packet,
                        "packet_id": "current-editable-packet",
                        "body_file": (
                            self.packet_fixture_dir / "bodies" / "valid-single-edited.md"
                        ).relative_to(self.packet_root).as_posix(),
                        "validation_result_path": (
                            "specs/fixture-pr-packet/.process/"
                            "pr-packets/current-editable-packet/validation.json"
                        ),
                    }
                ),
                encoding="utf-8",
            )
            completed, response, stderr_records = self.run_packet_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    {"packet_path": packet.relative_to(self.packet_root).as_posix()},
                )
            )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        self.assertEqual(response["data"]["stdout_json"]["status"], "passed")
        self.assertFalse(response["data"]["stdout_json"]["pr_blocked"])
        self.assertFalse(response["data"]["writes_state"])
        self.assertEqual(response["data"]["promotion_status"], "python_authoritative")
        self.assertEqual(stderr_records, [])

    def test_validate_pr_packet_reports_unsupported_platform_for_descriptorless_reads(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet unsupported-platform case")
        from speckit_pro_runner.helpers import read_only

        valid_packet_path = self.packet_fixture_dir / "valid-single.json"
        with patch.object(read_only, "descriptor_read_supported", return_value=False):
            result = read_only.validate_pr_packet_read_only(
                {"packet_path": valid_packet_path.relative_to(self.packet_root).as_posix()},
                self.packet_root,
            )
        payload = json.loads(result["stdout"])
        self.assertEqual(result["exit_code"], 2)
        self.assertEqual(payload["error_class"], "unsupported_platform")
        self.assertEqual(payload["failures"][0]["rule"], "input.unsupported_platform")
        schema = json.loads(PR_PACKET_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            read_only.json_schema_failures(payload, schema["$defs"]["validation_result"], schema, "validation_result"),
            [],
        )

    def test_validate_pr_packet_rejects_packet_id_that_disagrees_with_filename(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet identity case")
        valid_packet = json.loads((self.packet_fixture_dir / "valid-single.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            packet = Path(project) / "expected-id.json"
            packet.write_text(
                json.dumps(
                    {
                        **valid_packet,
                        "packet_id": "wrong-id",
                        "validation_result_path": (
                            "specs/fixture-pr-packet/.process/"
                            "pr-packets/expected-id/validation.json"
                        ),
                    }
                ),
                encoding="utf-8",
            )
            completed, response, stderr_records = self.run_packet_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    {"packet_path": packet.relative_to(self.packet_root).as_posix()},
                )
            )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        rules = {
            failure["rule"]
            for failure in response["data"]["stdout_json"]["failures"]
        }
        self.assertIn("input.identity.packet_id", rules)
        self.assertEqual(stderr_records, response["diagnostics"])

    def test_validate_pr_packet_fingerprint_covers_pre_h1_trailing_and_crossed_markers(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet protected body coverage case")
        valid_packet = json.loads((self.packet_fixture_dir / "valid-single.json").read_text(encoding="utf-8"))
        body_text = (self.packet_fixture_dir / "bodies" / "valid-single.md").read_text(encoding="utf-8")
        body_lines = body_text.splitlines()
        h1_index = next(index for index, line in enumerate(body_lines) if line.startswith("# "))
        late_h1_body = "\n".join(body_lines[:h1_index] + body_lines[h1_index + 1 :] + [body_lines[h1_index]]) + "\n"
        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            project_path = Path(project)
            cases = {
                "pre_h1": (
                    "<!-- unexpected protected preface -->\n" + body_text,
                    {"body.protected_fingerprint"},
                ),
                "trailing": (
                    body_text + "\n## Release Notes\n\nUnexpected protected trailer.\n",
                    {"body.protected_fingerprint"},
                ),
                "late_h1": (
                    late_h1_body,
                    {"body.title", "body.protected_fingerprint"},
                ),
                "crossed_marker": (
                    body_text.replace(
                        "<!-- speckit-pro-editable:summary:end -->\n\nSource:",
                        "Source:",
                        1,
                    ).replace(
                        "<!-- speckit-pro-editable:what_changed:start -->",
                        "<!-- speckit-pro-editable:what_changed:start -->\n<!-- speckit-pro-editable:summary:end -->",
                        1,
                    ),
                    {"body.editable_markers"},
                ),
            }
            for name, (mutated_body, expected_rules) in cases.items():
                with self.subTest(name=name):
                    body = project_path / f"{name}.md"
                    body.write_text(mutated_body, encoding="utf-8")
                    packet = project_path / f"{name}.json"
                    packet.write_text(
                        json.dumps(
                            {
                                **valid_packet,
                                "packet_id": f"{name}-packet",
                                "body_file": body.relative_to(self.packet_root).as_posix(),
                                "validation_result_path": (
                                    "specs/fixture-pr-packet/.process/"
                                    f"pr-packets/{name}-packet/validation.json"
                                ),
                            }
                        ),
                        encoding="utf-8",
                    )
                    completed, response, stderr_records = self.run_packet_runner(
                        helper_request(
                            "validate-pr-packet-read-only",
                            {"packet_path": packet.relative_to(self.packet_root).as_posix()},
                        )
                    )
                    self.assertEqual(completed.returncode, 1)
                    self.assert_response(response, "expected_failure", 1)
                    rules = {
                        failure["rule"]
                        for failure in response["data"]["stdout_json"]["failures"]
                    }
                    self.assertTrue(expected_rules.issubset(rules))
                    self.assertEqual(stderr_records, response["diagnostics"])

    def draft_packet_fixture(self) -> dict[str, object]:
        return json.loads((self.packet_fixture_dir / "valid-draft.json").read_text(encoding="utf-8"))

    def draft_packet_variant(self, packet_id: str, **overrides: object) -> dict[str, object]:
        """Re-own a draft packet copy so identity checks stay quiet on the variant."""
        return {
            **self.draft_packet_fixture(),
            "packet_id": packet_id,
            "validation_result_path": f"{DRAFT_PACKET_VALIDATION_DIR}/{packet_id}/validation.json",
            **overrides,
        }

    def packet_failure_rules(self, packet: Path) -> set[str]:
        completed, response, stderr_records = self.run_packet_runner(
            helper_request(
                "validate-pr-packet-read-only",
                {"packet_path": packet.relative_to(self.packet_root).as_posix()},
            )
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        self.assertEqual(stderr_records, response["diagnostics"])
        return {failure["rule"] for failure in response["data"]["stdout_json"]["failures"]}

    def test_validate_pr_packet_accepts_draft_without_verification_or_uat_evidence(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet draft acceptance case")
        draft_packet = self.draft_packet_fixture()
        self.assertEqual(draft_packet["verification_evidence"], [])
        self.assertEqual(draft_packet["scope_evidence"]["changed_files"], [])
        self.assertEqual(draft_packet["uat"]["how_to_uat"], "")
        self.assertEqual(draft_packet["uat"]["uat_runbook_heading"], "")
        self.assertTrue(draft_packet["uat"]["uat_source"])
        # Non-goals are the one piece of scope evidence a plan stage already has,
        # so draft mode must not relax them.
        self.assertTrue(draft_packet["scope_evidence"]["non_goals"])
        self.assertEqual(draft_packet["required_headings"], ["Artifacts", "Resume"])
        self.assertEqual(draft_packet["editable_fields"], [])
        self.assertEqual(draft_packet["protected_body_fingerprint"]["elided_fields"], [])
        self.assertNotIn("split_slice", draft_packet)

        completed, response, stderr_records = self.run_packet_runner(
            helper_request(
                "validate-pr-packet-read-only",
                {
                    "packet_path": (self.packet_fixture_dir / "valid-draft.json")
                    .relative_to(self.packet_root)
                    .as_posix()
                },
            )
        )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        payload = response["data"]["stdout_json"]
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["mode"], "draft")
        self.assertEqual(payload["failures"], [])
        self.assertFalse(payload["pr_blocked"])
        self.assertEqual(set(payload["source_fingerprints"]), {"body", "packet"})
        self.assertFalse(response["data"]["writes_state"])
        self.assertEqual(stderr_records, [])

        from speckit_pro_runner.helpers import read_only

        # The validation_result mode enum is the schema's second mode site. If only
        # the top-level enum learns draft, a passing draft packet's own validation
        # record stays unrepresentable.
        schema = json.loads(PR_PACKET_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            read_only.json_schema_failures(
                payload, schema["$defs"]["validation_result"], schema, "validation_result"
            ),
            [],
        )

    def test_validate_pr_packet_rejects_draft_that_carries_split_slice(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet draft split_slice case")
        split_packet = json.loads(
            (self.packet_fixture_dir / "valid-split.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            packet = Path(project) / "draft-with-slice.json"
            packet.write_text(
                json.dumps(
                    self.draft_packet_variant(
                        "draft-with-slice",
                        split_slice=split_packet["split_slice"],
                    )
                ),
                encoding="utf-8",
            )
            rules = self.packet_failure_rules(packet)
        # Only the split branch's else arm may object: a schema-clean split_slice
        # on a draft packet is forbidden, and nothing else about the packet is.
        self.assertEqual(rules, {"packet.schema.not"})

    def test_validate_pr_packet_rejects_draft_body_missing_a_required_heading(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet draft heading case")
        from speckit_pro_runner.helpers import read_only

        body_text = (self.packet_fixture_dir / "bodies" / "valid-draft.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            project_path = Path(project)
            for heading in ("## Artifacts", "## Resume"):
                packet_id = f"draft-missing-{heading[3:].lower()}"
                with self.subTest(missing=heading):
                    mutated = (
                        "\n".join(line for line in body_text.splitlines() if line != heading) + "\n"
                    )
                    body = project_path / f"{packet_id}.md"
                    body.write_text(mutated, encoding="utf-8")
                    packet = project_path / f"{packet_id}.json"
                    packet.write_text(
                        json.dumps(
                            self.draft_packet_variant(
                                packet_id,
                                body_file=body.relative_to(self.packet_root).as_posix(),
                                protected_body_fingerprint={
                                    **self.draft_packet_fixture()["protected_body_fingerprint"],
                                    "value": read_only.protected_body_sha256(mutated),
                                },
                            )
                        ),
                        encoding="utf-8",
                    )
                    # Fingerprint is recomputed for the mutated body, so the missing
                    # heading is the only thing left for the validator to object to.
                    self.assertEqual(self.packet_failure_rules(packet), {"body.required_headings"})

    def test_validate_pr_packet_accepts_draft_body_whose_artifacts_table_holds_only_gap_rows(
        self,
    ) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet draft zero-artifact case")
        from speckit_pro_runner.helpers import read_only

        draft_packet = self.draft_packet_fixture()
        gap_body = (
            f"# {draft_packet['generated_title']['value']}\n"
            "\n"
            "## Artifacts\n"
            "\n"
            "| Artifact | Purpose | Open |\n"
            "| --- | --- | --- |\n"
            "| Gap: Implementation Plan | Not generated for this run. | Not available |\n"
            "| Gap: Spec Explainer | Not generated for this run. | Not available |\n"
            "\n"
            "## Resume\n"
            "\n"
            "Stage: plan, stopped at the plan-stage boundary for review.\n"
            "Resume with: `/speckit-pro:speckit-autopilot <workflow-file> --stage implement`\n"
        )
        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            project_path = Path(project)
            body = project_path / "draft-gap-rows.md"
            body.write_text(gap_body, encoding="utf-8")
            packet = project_path / "draft-gap-rows.json"
            packet.write_text(
                json.dumps(
                    self.draft_packet_variant(
                        "draft-gap-rows",
                        body_file=body.relative_to(self.packet_root).as_posix(),
                        protected_body_fingerprint={
                            **draft_packet["protected_body_fingerprint"],
                            "value": read_only.protected_body_sha256(gap_body),
                        },
                    )
                ),
                encoding="utf-8",
            )
            completed, response, stderr_records = self.run_packet_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    {"packet_path": packet.relative_to(self.packet_root).as_posix()},
                )
            )
        # A run that generated no artifact still opens a valid draft.
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        self.assertEqual(response["data"]["stdout_json"]["status"], "passed")
        self.assertEqual(response["data"]["stdout_json"]["failures"], [])
        self.assertEqual(stderr_records, [])

    def test_validate_pr_packet_still_rejects_an_unknown_mode_value(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet unknown mode case")
        valid_packet = json.loads(
            (self.packet_fixture_dir / "valid-single.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            packet = Path(project) / "unknown-mode.json"
            for mode in ("sketch", "DRAFT", ""):
                with self.subTest(mode=mode):
                    packet.write_text(
                        json.dumps(
                            {
                                **valid_packet,
                                "packet_id": "unknown-mode",
                                "mode": mode,
                                "validation_result_path": (
                                    "specs/fixture-pr-packet/.process/"
                                    "pr-packets/unknown-mode/validation.json"
                                ),
                            }
                        ),
                        encoding="utf-8",
                    )
                    # Widening the enum to admit draft must not admit anything else,
                    # and the enum stays case-sensitive.
                    self.assertEqual(self.packet_failure_rules(packet), {"packet.schema.enum"})

    def test_validate_pr_packet_rejects_draft_required_headings_other_than_the_two_draft_blocks(
        self,
    ) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet draft required-headings case")
        cases = {
            "too-few": (["Artifacts"], {"packet.schema.min_items"}),
            "out-of-order": (
                ["Resume", "Artifacts"],
                {"packet.schema.const", "body.required_headings"},
            ),
            "too-many": (
                ["Artifacts", "Resume", "Known Gaps"],
                {"packet.schema.max_items", "body.required_headings"},
            ),
        }
        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            project_path = Path(project)
            for name, (required_headings, expected_rules) in cases.items():
                with self.subTest(name=name):
                    packet_id = f"draft-headings-{name}"
                    packet = project_path / f"{packet_id}.json"
                    packet.write_text(
                        json.dumps(
                            self.draft_packet_variant(
                                packet_id, required_headings=required_headings
                            )
                        ),
                        encoding="utf-8",
                    )
                    self.assertEqual(self.packet_failure_rules(packet), expected_rules)

    def test_validate_pr_packet_rejects_draft_that_declares_editable_fields(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet draft editable-fields case")
        valid_packet = json.loads(
            (self.packet_fixture_dir / "valid-single.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            packet = Path(project) / "draft-editable-fields.json"
            packet.write_text(
                json.dumps(
                    self.draft_packet_variant(
                        "draft-editable-fields",
                        editable_fields=valid_packet["editable_fields"][:1],
                    )
                ),
                encoding="utf-8",
            )
            rules = self.packet_failure_rules(packet)
        # The schema caps draft editable_fields at zero, and the draft body carries
        # no editable markers for the declared field to bind to.
        self.assertEqual(rules, {"packet.schema.max_items", "body.editable_markers"})

    def test_validate_pr_packet_still_rejects_single_required_headings_that_are_not_reviewer_set(
        self,
    ) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-packet-read-only":
            self.skipTest("validate-pr-packet single required-headings regression case")
        valid_packet = json.loads(
            (self.packet_fixture_dir / "valid-single.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory(dir=self.packet_root / "scratch") as project:
            packet = Path(project) / "single-draft-headings.json"
            packet.write_text(
                json.dumps(
                    {
                        **valid_packet,
                        "packet_id": "single-draft-headings",
                        "required_headings": ["Artifacts", "Resume"],
                        "validation_result_path": (
                            "specs/fixture-pr-packet/.process/"
                            "pr-packets/single-draft-headings/validation.json"
                        ),
                    }
                ),
                encoding="utf-8",
            )
            rules = self.packet_failure_rules(packet)
        # Moving the reviewer-heading constraint into the else arm must keep binding
        # single mode. If the else arm were omitted, only body.required_headings
        # would survive here.
        self.assertEqual(
            rules,
            {"packet.schema.const", "packet.schema.min_items", "body.required_headings"},
        )

    def test_validate_pr_workflow_contract_changed_files_is_canonicalized_and_evaluated(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-workflow-contract":
            self.skipTest("validate-pr-workflow-contract changed-files case")
        with helper_project() as root:
            project_path = root / "scratch"
            project_path.mkdir()
            changed_files = project_path / "changed-files.txt"
            changed_files.write_text(f"{ARCHIVED_FEATURE_DIR}/plan.md\n", encoding="utf-8")
            redundant_changed_files = f"{project_path.relative_to(root).as_posix()}/../{project_path.name}/changed-files.txt"
            response = self.assert_helper_matches_bash_reference(
                "validate-pr-workflow-contract",
                {
                    "title": "feat(OTHER): Wrong scope",
                    "repo_root": ".",
                    "changed_files": redundant_changed_files,
                },
                cwd=root,
            )
        self.assertEqual(response["data"]["argv"][-2:], ["-m", "speckit_pro_runner"])
        failures = response["data"]["stdout_json"]["failures"]
        self.assertEqual(failures[0]["rule"], "title.spec_scope")

    def test_validate_pr_workflow_contract_unreadable_changed_files_is_input_error(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-workflow-contract":
            self.skipTest("validate-pr-workflow-contract changed-files read-error case")
        with helper_project() as project:
            changed_files = project / "changed-files.txt"
            changed_files.write_text(f"{FEATURE_DIR}/plan.md\n", encoding="utf-8")
            from speckit_pro_runner.helpers import read_only

            with patch.object(read_only, "trusted_text", return_value=None):
                result = read_only.validate_pr_workflow_contract(
                    {
                        "title": "feat(FEATURE-001): Scope check",
                        "repo_root": ".",
                        "changed_files": changed_files.name,
                    },
                    project,
                )
        self.assertEqual(result["exit_code"], 2)
        self.assertEqual(result["stdout"], "")
        self.assertIn("changed-files list not readable", result["stderr"])

    def test_validate_pr_workflow_contract_matches_bash_when_origin_main_is_missing(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-pr-workflow-contract":
            self.skipTest("validate-pr-workflow-contract missing-origin case")
        from speckit_pro_runner.helpers.read_only import validate_pr_workflow_contract

        with patch("speckit_pro_runner.helpers.read_only.git_diff_changed_paths", return_value=None):
            result = validate_pr_workflow_contract(
                {
                    "title": "feat(FEATURE-001): Scope check",
                    "repo_root": ".",
                },
                REPO_ROOT,
            )
        self.assertEqual(result["exit_code"], 2)
        self.assertEqual(result["stdout"], "")
        self.assertIn("missing --changed-files and origin/main is unavailable", result["stderr"])

    def test_git_branch_rejects_untrusted_gitdir_pointer(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git branch pointer case uses check-prerequisites")
        with tempfile.TemporaryDirectory(prefix="helper-worktree-") as project, tempfile.TemporaryDirectory() as outside:
            project_path = Path(project).resolve()
            (project_path / ".git").write_text(f"gitdir: {outside}\n", encoding="utf-8")
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "")

    @staticmethod
    def _build_linked_worktree(
        workspace: Path,
        checkout_parent: Path,
        *,
        worktree_relpath: str,
        branch: str,
        backpointer: str | None = "self",
        admin_name: str | None = None,
    ) -> Path:
        """Build a git worktree the way git actually lays one out.

        Git records the link in both directions: the worktree's ``.git`` file
        points at ``<checkout>/.git/worktrees/<name>``, and that admin directory
        holds a ``gitdir`` file pointing back at the worktree's own ``.git``.
        ``backpointer`` selects what the admin directory records — ``"self"`` for
        the honest link, ``None`` to omit it, or a literal path to forge one.
        """
        project_path = workspace / worktree_relpath
        project_path.mkdir(parents=True)
        checkout_root = checkout_parent / REPO_ROOT.name
        git_dir = checkout_root / ".git" / "worktrees" / (admin_name or Path(worktree_relpath).name)
        (checkout_root / "speckit-pro" / "speckit_pro_runner").mkdir(parents=True)
        git_dir.mkdir(parents=True)
        (git_dir / "HEAD").write_text(f"ref: refs/heads/{branch}\n", encoding="utf-8")
        (project_path / ".git").write_text(f"gitdir: {git_dir}\n", encoding="utf-8")
        if backpointer == "self":
            (git_dir / "gitdir").write_text(f"{project_path / '.git'}\n", encoding="utf-8")
        elif backpointer is not None:
            (git_dir / "gitdir").write_text(f"{backpointer}\n", encoding="utf-8")
        return project_path

    def test_git_branch_accepts_worktree_named_for_its_branch(self) -> None:
        """The repository's own convention: .worktrees/<branch-name>.

        The worktree directory is named for the branch, never for the checkout,
        so a check that compares those two names rejects every feature worktree
        this repository creates.
        """
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git branch worktree metadata case uses check-prerequisites")
        with tempfile.TemporaryDirectory(prefix="helper-worktree-") as workspace, tempfile.TemporaryDirectory() as checkout_parent:
            project_path = self._build_linked_worktree(
                Path(workspace).resolve(),
                Path(checkout_parent).resolve(),
                worktree_relpath=".worktrees/fixture-archive-cleanup",
                branch="codex/fixture-archive-cleanup",
            )
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "codex/fixture-archive-cleanup")

    def test_git_branch_accepts_same_repo_worktree_metadata_name(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git branch worktree metadata case uses check-prerequisites")
        with tempfile.TemporaryDirectory(prefix="helper-worktree-") as workspace, tempfile.TemporaryDirectory() as checkout_parent:
            project_path = self._build_linked_worktree(
                Path(workspace).resolve(),
                Path(checkout_parent).resolve(),
                worktree_relpath=REPO_ROOT.name,
                branch="codex/fixture-archive-cleanup",
                admin_name=f"{REPO_ROOT.name}1",
            )
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "codex/fixture-archive-cleanup")

    def test_git_branch_rejects_worktree_metadata_without_backpointer(self) -> None:
        """A same-named directory is not proof of ownership.

        Name equality alone lets an unrelated checkout that merely shares a
        directory name supply HEAD. Git's own back-pointer is what proves the
        admin directory belongs to this worktree.
        """
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git branch worktree metadata case uses check-prerequisites")
        with tempfile.TemporaryDirectory(prefix="helper-worktree-") as workspace, tempfile.TemporaryDirectory() as checkout_parent:
            project_path = self._build_linked_worktree(
                Path(workspace).resolve(),
                Path(checkout_parent).resolve(),
                worktree_relpath=REPO_ROOT.name,
                branch="codex/fixture-archive-cleanup",
                backpointer=None,
            )
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "")

    def test_git_branch_rejects_worktree_metadata_pointing_elsewhere(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git branch worktree metadata case uses check-prerequisites")
        with tempfile.TemporaryDirectory(prefix="helper-worktree-") as workspace, tempfile.TemporaryDirectory() as checkout_parent, tempfile.TemporaryDirectory() as other:
            project_path = self._build_linked_worktree(
                Path(workspace).resolve(),
                Path(checkout_parent).resolve(),
                worktree_relpath=REPO_ROOT.name,
                branch="codex/fixture-archive-cleanup",
                backpointer=f"{Path(other) / '.git'}",
            )
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "")

    @staticmethod
    def _feature_state(project_path: Path, **inputs: object) -> dict[str, object]:
        from speckit_pro_runner.helpers.read_only import check_prerequisites

        result = check_prerequisites(dict(inputs), project_path)
        return json.loads(result["stdout"])

    def test_check_prerequisites_honors_feature_json_feature_directory(self) -> None:
        """`.specify/feature.json` is the sanctioned feature-state carrier.

        The vendored resolver reads it (scripts/bash/common.sh), so the runner
        must agree; otherwise the two implementations disagree about whether a
        run is on a feature, which is every spec this repository ships on a
        non-numeric branch.
        """
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("feature-state precedence case uses check-prerequisites")
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
            project_path = Path(project).resolve()
            (project_path / ".specify").mkdir()
            (project_path / ".specify" / "feature.json").write_text(
                '{"feature_directory":"specs/fixture-autopilot-staging"}\n', encoding="utf-8"
            )
            payload = self._feature_state(project_path)
            self.assertTrue(payload["on_feature_branch"])

    def setup_gate_for_spec(self, roadmap: str, spec_id: str) -> tuple[dict[str, object], int]:
        from speckit_pro_runner.helpers.read_only import reviewability_gate

        with helper_project() as project:
            (project / "roadmap.md").write_text(roadmap, encoding="utf-8")
            result = reviewability_gate(
                {"mode_name": "setup", "target": "roadmap.md", "spec_id": spec_id}, project,
            )
        return json.loads(result["stdout"]), int(result["exit_code"])

    def test_reviewability_setup_gate_reads_only_the_requested_spec_section(self) -> None:
        if self.helper_filter and self.helper_filter != "reviewability-gate":
            self.skipTest("setup spec-scope case uses reviewability-gate")
        roadmap = "# Demo Roadmap\n\n" + "".join((
            roadmap_budget_entry("SPEC-001", "Oversized first spec", "API", 900, 9, 30),
            roadmap_budget_entry("SPEC-002", "Middle spec", "UI", 120, 2, 5),
            roadmap_budget_entry("SPEC-003", "Small last spec", "docs/process", 40, 1, 3),
        ))
        payload, exit_code = self.setup_gate_for_spec(roadmap, "SPEC-001")
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "block")
        self.assertFalse(payload["pass"])
        self.assertEqual(payload["spec_id"], "SPEC-001")
        self.assertEqual(
            (payload["reviewable_loc"], payload["production_files"], payload["total_files"]), (900, 9, 30),
        )
        self.assertEqual(payload["primary_surfaces"], ["API"])
        self.assertNotIn("primary_surfaces", payload["thresholds"]["block"])
        self.assertEqual(payload["thresholds"]["block"]["reviewable_loc"], 800)
        self.assertFalse(any("primary surfaces" in warning for warning in payload["warnings"]))

        payload, exit_code = self.setup_gate_for_spec(roadmap, "SPEC-003")
        self.assertEqual((payload["status"], exit_code), ("pass", 0))
        self.assertEqual(payload["primary_surfaces"], ["docs/process"])

    def test_reviewability_setup_gate_honors_typed_exception_in_spec_section(self) -> None:
        if self.helper_filter and self.helper_filter != "reviewability-gate":
            self.skipTest("setup exception case uses reviewability-gate")
        entry = roadmap_budget_entry("SPEC-001", "Infra spec with a typed exception", "scheduler/runtime", 900, 9, 20)
        payload, exit_code = self.setup_gate_for_spec(
            f"# Demo Roadmap\n\n{entry}Reviewability-Exception: infra\n", "SPEC-001",
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "exception")
        self.assertTrue(payload["pass"])
        self.assertTrue(payload["exception_honored"])
        self.assertEqual(payload["exception_class"], "infra")
        self.assertEqual(payload["exceptions"]["accepted"], ["infra"])

        for pragma in ("Reviewability-Exception: <class>", "Reviewability-Exception: Infra",
                       "Reviewability-Exception: infra because it is big"):
            with self.subTest(pragma=pragma):
                payload, exit_code = self.setup_gate_for_spec(
                    f"# Demo Roadmap\n\n{entry}{pragma}\n", "SPEC-001",
                )
                self.assertEqual((payload["status"], exit_code), ("block", 1))
                self.assertFalse(payload["exception_honored"])
                self.assertIsNone(payload["exception_class"])
                self.assertEqual(payload["exceptions"]["rejected"], [pragma])

        other = roadmap_budget_entry("SPEC-002", "Other spec", "API", 100, 1, 2)
        payload, _ = self.setup_gate_for_spec(
            f"# Demo Roadmap\n\n{entry}{other}Reviewability-Exception: infra\n", "SPEC-001",
        )
        self.assertEqual(payload["status"], "block", "another section's pragma must not excuse SPEC-001")

    def test_reviewability_setup_gate_fails_closed_without_spec_budget(self) -> None:
        if self.helper_filter and self.helper_filter != "reviewability-gate":
            self.skipTest("setup missing-budget case uses reviewability-gate")
        roadmap = (
            "# Demo Roadmap\n\n### SPEC-001: Entry with no budget fields\n\n"
            "**Priority:** P1 | **Depends On:** None | **Enables:** None\n"
        )
        payload, exit_code = self.setup_gate_for_spec(roadmap, "SPEC-001")
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "block")
        self.assertFalse(payload["pass"])
        self.assertEqual(len(payload["blockers"]), 3)
        self.assertTrue(all("missing" in blocker for blocker in payload["blockers"]))

        payload, exit_code = self.setup_gate_for_spec(
            roadmap + "Reviewability-Exception: infra\n", "SPEC-001",
        )
        self.assertEqual((payload["status"], exit_code), ("block", 1), "a pragma never excuses a missing budget")

        payload, exit_code = self.setup_gate_for_spec(roadmap, "SPEC-009")
        self.assertEqual(exit_code, 2)
        self.assertIn("SPEC-009", payload["error"])

    def test_check_prerequisites_compares_the_cli_version_with_the_pin(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("CLI version case uses check-prerequisites")
        cases = (
            ("/fixture/bin/specify", "1.1.0", "match"),
            ("/fixture/bin/specify", "1.0.12", "older"),
            ("/fixture/bin/specify", "1.2.0", "newer"),
            ("/fixture/bin/specify", "1.10.0", "newer"),
            ("/fixture/bin/specify", "1.1.0.dev0", "unreadable"),
            ("/fixture/bin/specify", None, "unreadable"),
            (None, None, "missing"),
        )
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
            for executable, version, status in cases:
                with self.subTest(executable=executable, version=version), patch(
                    "speckit_pro_runner.helpers.read_only.find_specify", return_value=executable,
                ), patch(
                    "speckit_pro_runner.helpers.read_only.verified_specify_executable",
                    return_value=Path(executable) if executable else None,
                ), patch(
                    "speckit_pro_runner.helpers.read_only.installed_specify_version",
                    return_value=version,
                ):
                    payload = self._feature_state(Path(project))
                    row = next(item for item in payload["checks"] if item["check"] == "speckit_cli")
                    self.assertEqual(row["pass"], executable is not None)
                    spec_kit = payload["spec_kit"]
                    self.assertEqual(spec_kit["status"], status)
                    self.assertEqual(spec_kit["pinned_version"], "1.1.0")
                    expected_shown = None if executable is None else (
                        version if status in ("match", "older", "newer") else "unparsed")
                    self.assertEqual(spec_kit["installed_version"], expected_shown)
                    self.assertEqual(
                        spec_kit["install_argv"],
                        [
                            "uv", "tool", "install", "specify-cli", "--force", "--from",
                            "git+https://github.com/github/spec-kit.git"
                            "@f1d3a4f8337ebbd3ae22760a9c12e3352b93a175",
                        ],
                    )
                    if executable is not None:
                        version_row = next(
                            item for item in payload["checks"] if item["check"] == "speckit_cli_version"
                        )
                        self.assertTrue(version_row["pass"], "a version mismatch never stops a run")

    def test_spec_kit_state_never_echoes_raw_cli_output_or_the_home_path(self) -> None:
        from speckit_pro_runner.helpers.read_only import installed_specify_version, spec_kit_cli_state

        hostile = "9" * 5000 + "\x1b[31m"
        with patch(
            "speckit_pro_runner.helpers.read_only.installed_specify_version", return_value=hostile,
        ), patch(
            "speckit_pro_runner.helpers.read_only.verified_specify_executable",
            return_value=Path.home() / ".local" / "bin" / "specify",
        ):
            rows, state = spec_kit_cli_state(str(Path.home() / ".local" / "bin" / "specify"))
        self.assertEqual(state["installed_version"], "unparsed")
        self.assertEqual(state["status"], "unreadable")
        detail = rows[0]["detail"]
        self.assertNotIn(hostile[:20], detail)
        self.assertNotIn(str(Path.home()), detail)
        self.assertTrue(detail.startswith("~/.local/bin/specify"))
        seen = []
        stdout = "padding " * 1000 + "CLI Version    1.1.0"
        with patch(
            "speckit_pro_runner.helpers.read_only.subprocess.run",
            return_value=SimpleNamespace(stdout=stdout, returncode=0),
        ), patch("speckit_pro_runner.helpers.read_only.shutil.which", return_value="/fixture/bin/specify"), patch(
            "speckit_pro_runner.helpers.read_only.trusted_executable", return_value=Path("/fixture/bin/specify"),
        ), patch(
            "speckit_pro_runner.helpers.read_only.executable_path", return_value=Path("/fixture/bin/specify"),
        ), patch(
            "speckit_pro_runner.helpers.read_only.spec_kit_pin.parse_cli_version",
            side_effect=lambda text: seen.append(len(text)),
        ):
            installed_specify_version("/fixture/bin/specify")
        self.assertEqual(seen, [4096])

    def test_installed_specify_version_reads_the_cli_version_row(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("CLI version case uses check-prerequisites")
        from speckit_pro_runner.helpers.read_only import installed_specify_version

        panel = (
            "╭──── Specify CLI Information ────╮\n"
            "│                                 │\n"
            "│     CLI Version    1.0.12       │\n"
            "│          Python    3.13.13      │\n"
        )
        for stdout, returncode, expected in ((panel, 0, "1.0.12"), ("no row", 0, None), (panel, 2, None)):
            with self.subTest(returncode=returncode, stdout=stdout[:8]), patch(
                "speckit_pro_runner.helpers.read_only.subprocess.run",
                return_value=SimpleNamespace(stdout=stdout, returncode=returncode),
            ), patch(
                "speckit_pro_runner.helpers.read_only.shutil.which", return_value="/fixture/bin/specify",
            ), patch(
                "speckit_pro_runner.helpers.read_only.trusted_executable", return_value=Path("/fixture/bin/specify"),
            ), patch(
                "speckit_pro_runner.helpers.read_only.executable_path", return_value=Path("/fixture/bin/specify"),
            ):
                self.assertEqual(installed_specify_version("/fixture/bin/specify"), expected)
        with patch("speckit_pro_runner.helpers.read_only.subprocess.run", side_effect=OSError), patch(
            "speckit_pro_runner.helpers.read_only.shutil.which", return_value="/fixture/bin/specify",
        ), patch(
            "speckit_pro_runner.helpers.read_only.trusted_executable", return_value=Path("/fixture/bin/specify"),
        ), patch(
            "speckit_pro_runner.helpers.read_only.executable_path", return_value=Path("/fixture/bin/specify"),
        ):
            self.assertIsNone(installed_specify_version("/fixture/bin/specify"))

    def test_installed_specify_version_probes_the_resolved_fallback_binary(self) -> None:
        from speckit_pro_runner.helpers.read_only import find_specify, installed_specify_version

        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            alias = home / ".local" / "bin" / "specify.exe"
            attested = home / "trusted" / "bin" / "specify.exe"
            with patch("speckit_pro_runner.helpers.read_only.Path.home", return_value=home), patch(
                "speckit_pro_runner.helpers.read_only.sys.platform", "linux",
            ), patch(
                "speckit_pro_runner.helpers.read_only.shutil.which",
                side_effect=[None, str(alias), str(alias), str(attested), str(attested)],
            ) as which, patch(
                "speckit_pro_runner.helpers.read_only.trusted_executable",
                side_effect=[attested, attested],
            ), patch(
                "speckit_pro_runner.helpers.read_only.subprocess.run",
                return_value=SimpleNamespace(stdout="CLI Version    1.1.0", returncode=0),
            ) as run:
                selected = find_specify()
                self.assertEqual(selected, str(alias))
                self.assertEqual(installed_specify_version(selected), "1.1.0")
            self.assertEqual(which.call_args.kwargs["path"], str(attested.parent))
            self.assertEqual(run.call_args.args[0], [str(attested), "version"])
            self.assertNotIn("executable", run.call_args.kwargs)
            self.assertFalse(run.call_args.kwargs["shell"])
            self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)

    def test_installed_specify_version_never_probes_a_workspace_executable(self) -> None:
        from speckit_pro_runner.helpers.read_only import installed_specify_version

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            binary = workspace / "specify.exe"
            binary.touch()
            binary.chmod(0o755)
            for candidate in (str(binary), "specify.exe"):
                with self.subTest(candidate=candidate), patch(
                    "speckit_pro_runner.helpers.read_only.Path.cwd", return_value=workspace,
                ), patch("speckit_pro_runner.helpers.read_only.sys.platform", "win32"), patch(
                    "speckit_pro_runner.helpers.read_only.shutil.which", return_value=candidate,
                ), patch(
                    "speckit_pro_runner.helpers.read_only.subprocess.run",
                    return_value=SimpleNamespace(stdout="CLI Version    1.1.0", returncode=0),
                ) as run:
                    self.assertIsNone(installed_specify_version(candidate))
                    run.assert_not_called()

    def test_installed_specify_version_accepts_windows_file_modes(self) -> None:
        from speckit_pro_runner.helpers.read_only import installed_specify_version

        with tempfile.TemporaryDirectory() as temporary:
            binary = Path(temporary).resolve() / "specify.exe"
            binary.touch()
            binary.chmod(0o755)
            with patch("speckit_pro_runner.helpers.read_only.sys.platform", "win32"), patch(
                "speckit_pro_runner.helpers.read_only.shutil.which", return_value=str(binary),
            ), patch(
                "speckit_pro_runner.codex_launch.Path.stat", return_value=SimpleNamespace(st_mode=0o100666),
            ), patch(
                "speckit_pro_runner.helpers.read_only.subprocess.run",
                return_value=SimpleNamespace(stdout="CLI Version    1.1.0", returncode=0),
            ) as run:
                self.assertEqual(installed_specify_version(str(binary)), "1.1.0")
                self.assertEqual(run.call_args.args[0], [str(binary), "version"])
                self.assertNotIn("executable", run.call_args.kwargs)

    def test_installed_specify_version_rejects_a_reselected_or_symlinked_workspace_binary(self) -> None:
        from speckit_pro_runner.helpers.read_only import installed_specify_version

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            workspace = root / "checkout"
            workspace.mkdir()
            installed = root / "bin" / "specify"
            installed.parent.mkdir()
            installed.touch()
            installed.chmod(0o755)
            workspace_binary = workspace / "specify.exe"
            workspace_binary.touch()
            workspace_binary.chmod(0o755)
            link = installed.parent / "specify.exe"
            link.symlink_to(workspace_binary)
            checkout_link = workspace / "bin" / "specify.exe"
            checkout_link.parent.mkdir()
            checkout_link.symlink_to(installed)
            for selected, candidate in ((installed, workspace_binary), (link, link), (checkout_link, checkout_link)):
                with self.subTest(selected=selected.name), patch(
                    "speckit_pro_runner.helpers.read_only.Path.cwd", return_value=workspace,
                ), patch("speckit_pro_runner.helpers.read_only.sys.platform", "win32"), patch(
                    "speckit_pro_runner.helpers.read_only.shutil.which", return_value=str(candidate),
                ), patch("speckit_pro_runner.helpers.read_only.subprocess.run") as run:
                    self.assertIsNone(installed_specify_version(str(selected)))
                    run.assert_not_called()

    def test_spec_kit_cli_state_blocks_workspace_and_cwd_candidates(self) -> None:
        from speckit_pro_runner.helpers.read_only import spec_kit_cli_state

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            workspace = root / "checkout"
            workspace.mkdir()
            for binary in (workspace / "specify.exe", root / "specify.exe"):
                binary.touch()
                binary.chmod(0o755)
                with self.subTest(parent=binary.parent.name), patch(
                    "speckit_pro_runner.helpers.read_only.Path.cwd", return_value=root,
                ), patch(
                    "speckit_pro_runner.helpers.read_only.shutil.which", return_value=str(binary),
                ), patch("speckit_pro_runner.helpers.read_only.subprocess.run") as run:
                    rows, state = spec_kit_cli_state(str(binary), workspace)
                    self.assertEqual(state["status"], "missing")
                    self.assertEqual(state["cli_argv"], [])
                    self.assertFalse(rows[0]["pass"])
                    run.assert_not_called()

    def test_installed_specify_version_treats_decoding_failure_as_unreadable(self) -> None:
        from speckit_pro_runner.helpers.read_only import installed_specify_version, spec_kit_cli_state

        error = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
        with patch("speckit_pro_runner.helpers.read_only.subprocess.run", side_effect=error), patch(
            "speckit_pro_runner.helpers.read_only.shutil.which", return_value="/fixture/bin/specify",
        ), patch(
            "speckit_pro_runner.helpers.read_only.trusted_executable", return_value=Path("/fixture/bin/specify"),
        ), patch(
            "speckit_pro_runner.helpers.read_only.executable_path", return_value=Path("/fixture/bin/specify"),
        ):
            self.assertIsNone(installed_specify_version("/fixture/bin/specify"))
            rows, state = spec_kit_cli_state("/fixture/bin/specify")
        self.assertEqual(state["status"], "unreadable")
        self.assertTrue(all(row["pass"] for row in rows))

    def test_spec_kit_release_version_accepts_only_short_ascii_components(self) -> None:
        from speckit_pro_runner import spec_kit_pin

        for hostile in ("\u0661.\u0661.\u0660", "\uff11.\uff11.\uff10", "1." + "1" * 3000 + ".0", "1.1.1234567"):
            with self.subTest(version=hostile[:12]):
                self.assertIsNone(spec_kit_pin.release_version(hostile))
                self.assertEqual(spec_kit_pin.version_status(hostile, cli_found=True), "unreadable")
        self.assertEqual(spec_kit_pin.release_version("1.1.0"), "1.1.0")
        self.assertEqual(spec_kit_pin.release_version("123456.0.1"), "123456.0.1")

    def test_cli_path_detail_never_shows_another_users_path(self) -> None:
        from speckit_pro_runner.helpers.read_only import _home_relative

        home = Path.home()
        self.assertEqual(_home_relative(str(home / ".local" / "bin" / "specify")), "~/.local/bin/specify")
        other_home = Path(Path.home().anchor) / "elsewhere" / "other-person" / "bin" / "specify"
        self.assertEqual(_home_relative(str(other_home)), "specify")
        self.assertEqual(_home_relative("specify"), "specify")
        self.assertEqual(_home_relative(str(home / ".." / "other-person" / "bin" / "specify")), "specify")

    def test_spec_kit_version_ordering_compares_numeric_components(self) -> None:
        from speckit_pro_runner import spec_kit_pin

        for pinned, installed, status in (
            ("1.9.9", "1.10.0", "newer"),
            ("1.10.0", "1.9.99", "older"),
        ):
            with self.subTest(pinned=pinned, installed=installed), patch.object(
                spec_kit_pin, "PINNED_VERSION", pinned,
            ):
                self.assertEqual(spec_kit_pin.version_status(installed, cli_found=True), status)

    def test_check_prerequisites_honors_specify_feature_directory_env(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("feature-state precedence case uses check-prerequisites")
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
            project_path = Path(project).resolve()
            (project_path / ".specify").mkdir()
            with patch.dict(
                os.environ, {"SPECIFY_FEATURE_DIRECTORY": "specs/fixture-availability"}, clear=False
            ):
                payload = self._feature_state(project_path)
            self.assertTrue(payload["on_feature_branch"])

    def test_check_prerequisites_reports_no_feature_without_state_or_branch(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("feature-state precedence case uses check-prerequisites")
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
            project_path = Path(project).resolve()
            (project_path / ".specify").mkdir()
            environment = {
                key: value
                for key, value in os.environ.items()
                if key not in {"SPECIFY_FEATURE_DIRECTORY", "SPECIFY_FEATURE"}
            }
            with patch.dict(os.environ, environment, clear=True):
                payload = self._feature_state(project_path)
            self.assertFalse(payload["on_feature_branch"])

    def test_check_prerequisites_ignores_blank_feature_directory(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("feature-state precedence case uses check-prerequisites")
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
            project_path = Path(project).resolve()
            (project_path / ".specify").mkdir()
            (project_path / ".specify" / "feature.json").write_text(
                '{"feature_directory":"   "}\n', encoding="utf-8"
            )
            environment = {
                key: value
                for key, value in os.environ.items()
                if key not in {"SPECIFY_FEATURE_DIRECTORY", "SPECIFY_FEATURE"}
            }
            with patch.dict(os.environ, environment, clear=True):
                payload = self._feature_state(project_path)
            self.assertFalse(payload["on_feature_branch"])

    @staticmethod
    def _detected(project_path: Path) -> dict[str, object]:
        from speckit_pro_runner.helpers.read_only import detect_commands

        return json.loads(detect_commands({}, project_path)["stdout"])

    @staticmethod
    def _helper_json(helper: str, inputs: dict[str, object], project_path: Path) -> tuple[int, dict[str, object]]:
        from speckit_pro_runner.helpers import read_only

        result = getattr(read_only, helper)(inputs, project_path)
        return result["exit_code"], json.loads(result["stdout"])

    def test_clarification_counters_match_bare_and_colon_markers(self) -> None:
        """The spec template writes `[NEEDS CLARIFICATION: ...]`; every counter must see it."""
        if self.helper_filter and self.helper_filter not in {"validate-gate", "count-markers"}:
            self.skipTest("marker-form cases use validate-gate and count-markers")
        with helper_project() as project_path:
            feature = project_path / "specs" / "001-demo"
            feature.mkdir(parents=True)
            (feature / "spec.md").write_text(
                "- FR-001: Log in via [NEEDS CLARIFICATION: auth method not specified]\n"
                "- FR-002: Keep data for [NEEDS CLARIFICATION]\n"
                "The phrase NEEDS CLARIFICATION in plain prose is not a marker.\n"
                "Neither is [NEEDS CLARIFICATIONS] or (NEEDS CLARIFICATION: x).\n",
                encoding="utf-8",
            )
            (feature / "plan.md").write_text("Plan text [NEEDS CLARIFICATION: storage engine]\n", encoding="utf-8")
            inputs = {"feature_dir": "specs/001-demo"}
            for gate in ("G1", "G2"):
                with self.subTest(gate=gate):
                    code, payload = self._helper_json("validate_gate", {**inputs, "gate": gate}, project_path)
                    self.assertEqual(1, code)
                    self.assertFalse(payload["pass"])
                    self.assertEqual(2, payload["markers"])
                    self.assertEqual(2, len(payload["details"]))
            code, payload = self._helper_json("validate_gate", {**inputs, "gate": "G3"}, project_path)
            self.assertEqual(1, code)
            self.assertIn("NC:1", payload["reason"])
            code, payload = self._helper_json("count_markers", {**inputs, "type": "clarifications"}, project_path)
            self.assertEqual((0, 3, 2, 1), (code, payload["total"], payload["spec"], payload["plan"]))
            self.assertEqual(2, len(payload["details"]))
            code, payload = self._helper_json("count_markers", {**inputs, "type": "all"}, project_path)
            self.assertEqual(3, payload["clarifications"])
            (feature / "spec.md").write_text("The phrase NEEDS CLARIFICATION in prose only.\n", encoding="utf-8")
            code, payload = self._helper_json("validate_gate", {**inputs, "gate": "G2"}, project_path)
            self.assertEqual((0, True, 0), (code, payload["pass"], payload["markers"]))

    def test_validate_gate_g4_counts_checklist_gaps(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-gate":
            self.skipTest("G4 checklist case uses validate-gate")
        with helper_project() as project_path:
            feature = project_path / "specs" / "001-demo"
            (feature / "checklists").mkdir(parents=True)
            (feature / "spec.md").write_text("spec\n", encoding="utf-8")
            (feature / "plan.md").write_text("plan\n", encoding="utf-8")
            (feature / "checklists" / "security.md").write_text(
                "- [ ] CHK001 Is token expiry defined? [Gap]\n- [ ] CHK002 Are roles listed? [Gap]\n", encoding="utf-8"
            )
            code, payload = self._helper_json("validate_gate", {"gate": "G4", "feature_dir": "specs/001-demo"}, project_path)
            self.assertEqual(1, code)
            self.assertEqual(2, payload["markers"])
            self.assertIn("checklists:2", payload["reason"])
            (feature / "checklists" / "security.md").write_text("- [x] CHK001 Is token expiry defined?\n", encoding="utf-8")
            code, payload = self._helper_json("validate_gate", {"gate": "G4", "feature_dir": "specs/001-demo"}, project_path)
            self.assertEqual((0, True), (code, payload["pass"]))

    def _g5(self, project_path: Path, tasks: str, depends_on: dict[str, list[str]] | None) -> tuple[int, dict[str, object]]:
        feature = project_path / "specs" / "001-demo"
        feature.mkdir(parents=True, exist_ok=True)
        (feature / "tasks.md").write_text(tasks, encoding="utf-8")
        if depends_on is not None:
            (feature / ".process").mkdir(exist_ok=True)
            sidecar = {
                "schema_version": "task-execution.v1",
                "fingerprints": {},
                "tasks": {
                    task_id: {"capability_group": "demo", "depends_on": deps, "owns": ["src"], "tdd_unit": task_id.lower()}
                    for task_id, deps in depends_on.items()
                },
            }
            (feature / ".process" / "task-execution.json").write_text(json.dumps(sidecar), encoding="utf-8")
        return self._helper_json("validate_gate", {"gate": "G5", "feature_dir": "specs/001-demo"}, project_path)

    G5_LOOP_TASKS = (
        "## Phase 1: Setup\n\n"
        + "- [ ] T001 Inventory the candidate PR markers and reconcile them against the first actual implementation checkpoint\n"
        + "- [ ] T002 Confirm the marker plan recorded by T001\n\n"
        + "## Phase 3: User Story 1\n\n"
        + "- [ ] T003 [US1] Implement the parser in src/parser.py\n"
    )

    G5_LOOP_DEPENDS = {"T001": [], "T002": ["T001"], "T003": ["T002"]}

    def test_validate_gate_g5_rejects_a_gate_task_that_waits_on_its_dependents(self) -> None:
        """#773: a setup gate that needs implementation evidence can never complete."""
        if self.helper_filter and self.helper_filter != "validate-gate":
            self.skipTest("G5 gate-task loop case uses validate-gate")
        with helper_project() as project_path:
            code, payload = self._g5(project_path, self.G5_LOOP_TASKS, self.G5_LOOP_DEPENDS)
        self.assertEqual((1, False), (code, payload["pass"]))
        self.assertEqual(3, payload["task_count"])
        loops = payload["gate_task_loops"]
        self.assertEqual(["T001"], [loop["task"] for loop in loops])
        self.assertEqual(["T002", "T003"], loops[0]["dependents"])
        self.assertEqual("first actual implementation checkpoint", loops[0]["evidence"])
        detail = " ".join(payload["details"])
        self.assertIn("T001", detail)
        self.assertIn("Split it", detail)
        self.assertIn("candidate check", detail)
        self.assertIn("emission step", detail)

    def test_validate_gate_g5_passes_the_split_gate_form(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-gate":
            self.skipTest("G5 gate-task loop case uses validate-gate")
        tasks = (
            "## Phase 1: Setup\n\n"
            + "- [ ] T001 Inventory the candidate PR markers as a candidate check\n"
            + "- [ ] T002 Confirm the candidate marker plan recorded by T001\n\n"
            + "## Phase 3: User Story 1\n\n"
            + "- [ ] T003 [US1] Implement the parser in src/parser.py\n\n"
            + "## Phase 4: Polish & Cross-Cutting Concerns\n\n"
            + "- [ ] T004 Before PR emission, reconcile the markers against the actual per-PR diff, actual LOC and checkpoint evidence\n"
            + "- [ ] T005 Emit the PR body from the reconciled markers of T004\n"
        )
        depends = {"T001": [], "T002": ["T001"], "T003": ["T002"], "T004": ["T003"], "T005": ["T004"]}
        with helper_project() as project_path:
            code, payload = self._g5(project_path, tasks, depends)
        self.assertEqual((0, True), (code, payload["pass"]), payload)
        self.assertNotIn("gate_task_loops", payload)

    def test_validate_gate_g5_passes_a_gate_that_only_names_the_later_emission_step(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-gate":
            self.skipTest("G5 gate-task loop case uses validate-gate")
        tasks = self.G5_LOOP_TASKS.replace(
            "reconcile them against the first actual implementation checkpoint",
            "check them now; reconciliation against the actual diff happens later in T004 before PR emission",
        )
        with helper_project() as project_path:
            code, payload = self._g5(project_path, tasks, self.G5_LOOP_DEPENDS)
        self.assertEqual((0, True), (code, payload["pass"]), payload)

    def test_validate_gate_g5_passes_a_stop_before_pr_emission_guard_clause(self) -> None:
        """#802: a stop condition timed before PR emission is not evidence the task's dependents produce."""
        if self.helper_filter and self.helper_filter != "validate-gate":
            self.skipTest("G5 gate-task loop case uses validate-gate")
        tasks = (
            "## Phase 3: User Story 1\n\n"
            + "- [ ] T001 [US1] Implement the parser in src/parser.py\n"
            + "- [ ] T002 [US1] Run the structural cases and record the slice paths and marker checkpoint; "
            + "stop before PR emission on any new path or failed gate\n\n"
            + "## Phase 4: User Story 2\n\n"
            + "- [ ] T003 [US2] Implement the writer in src/writer.py\n"
        )
        with helper_project() as project_path:
            code, payload = self._g5(project_path, tasks, {"T001": [], "T002": ["T001"], "T003": ["T002"]})
        self.assertEqual((0, True), (code, payload["pass"]), payload)
        self.assertNotIn("gate_task_loops", payload)

    def test_validate_gate_g5_uses_sidecar_dependents_outside_the_setup_phase(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-gate":
            self.skipTest("G5 gate-task loop case uses validate-gate")
        tasks = (
            "## Phase 3: User Story 1\n\n"
            + "- [ ] T001 [US1] Record the actual LOC before starting the parser\n"
            + "- [ ] T002 [US1] Implement the parser in src/parser.py\n"
        )
        with helper_project() as project_path:
            code, payload = self._g5(project_path, tasks, {"T001": [], "T002": ["T001"]})
            self.assertEqual((1, False), (code, payload["pass"]))
            self.assertEqual(["T002"], payload["gate_task_loops"][0]["dependents"])
            code, payload = self._g5(project_path, tasks, {"T001": [], "T002": []})
            self.assertEqual((0, True), (code, payload["pass"]), payload)
        with helper_project() as project_path:
            # Without a sidecar only the setup/foundation phase rule applies.
            code, payload = self._g5(project_path, tasks, None)
        self.assertEqual((0, True), (code, payload["pass"]), payload)

    def test_validate_gate_g5_ignores_completed_tasks_and_fails_closed_on_a_bad_sidecar(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-gate":
            self.skipTest("G5 gate-task loop case uses validate-gate")
        with helper_project() as project_path:
            done = self.G5_LOOP_TASKS.replace("- [ ] T001", "- [x] T001")
            code, payload = self._g5(project_path, done, self.G5_LOOP_DEPENDS)
            self.assertEqual((0, True), (code, payload["pass"]), payload)
            sidecar = project_path / "specs" / "001-demo" / ".process" / "task-execution.json"
            sidecar.write_text("{not json", encoding="utf-8")
            code, payload = self._g5(project_path, self.G5_LOOP_TASKS.replace("first actual implementation", "first"), None)
        self.assertEqual((1, False), (code, payload["pass"]))
        self.assertIn("validate-task-execution", payload["reason"])

    G5_COVERAGE_TASKS = (
        "## Phase 3: User Story 1\n\n"
        + "- [ ] T001 [US1] Implement the parser in src/parser.py\n"
        + "- [ ] T002 [US1] Implement the writer in src/writer.py\n\n"
        + "## Requirement Coverage\n\n"
        + "| Requirement | Tasks |\n"
        + "|---|---|\n"
        + "| FR-005 parse input | T001 (US1) |\n"
        + "| FR-006 write output |  () |\n"
        + "| FR-007 keep order |   |\n"
        + "| FR-008 report errors | T001, T002 |\n"
    )

    def test_validate_gate_g5_fails_empty_requirement_coverage_rows(self) -> None:
        """#794: a coverage row with an empty or placeholder task cell fails G5 and names the row."""
        if self.helper_filter and self.helper_filter != "validate-gate":
            self.skipTest("G5 coverage-row case uses validate-gate")
        with helper_project() as project_path:
            code, payload = self._g5(project_path, self.G5_COVERAGE_TASKS, None)
        self.assertEqual((1, False), (code, payload["pass"]), payload)
        self.assertEqual(["FR-006", "FR-007"], [row["requirement"] for row in payload["empty_coverage_rows"]])
        self.assertIn("2 requirement coverage row(s)", payload["reason"])
        detail = " ".join(payload["details"])
        self.assertIn("FR-006", detail)
        self.assertIn("FR-007", detail)
        self.assertIn("task IDs", detail)

    def test_validate_gate_g5_passes_filled_or_absent_coverage_tables(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-gate":
            self.skipTest("G5 coverage-row case uses validate-gate")
        filled = self.G5_COVERAGE_TASKS.replace("|  () |", "| T002 (US1) |").replace("|   |", "| T001-T002 |")
        other_table = self.G5_COVERAGE_TASKS.replace("| Requirement | Tasks |", "| Requirement | Notes |")
        absent = self.G5_COVERAGE_TASKS.split("## Requirement Coverage")[0]
        for name, tasks in (("filled", filled), ("no task column", other_table), ("no table", absent)):
            with self.subTest(case=name), helper_project() as project_path:
                code, payload = self._g5(project_path, tasks, None)
                self.assertEqual((0, True), (code, payload["pass"]), payload)
                self.assertNotIn("empty_coverage_rows", payload)

    def test_tasks_prompt_tells_the_producer_to_fill_every_coverage_row(self) -> None:
        template = Path(__file__).resolve().parents[3] / "speckit-pro/skills/speckit-coach/templates/workflow-template.md"
        text = template.read_text(encoding="utf-8")
        prompt = " ".join(text[text.index("### Tasks Prompt"):text.index("### Tasks Results")].split())
        self.assertIn("requirement coverage table", prompt)
        self.assertIn("every row", prompt)
        self.assertIn("G5 fails", prompt)

    @contextmanager
    def _g6_project(self) -> Iterator[Path]:
        """A clean planning tree: no bracketed severity marker in spec, plan, or tasks."""
        with helper_project() as project_path:
            feature = project_path / "specs" / "001-demo"
            feature.mkdir(parents=True)
            for name in ("spec.md", "plan.md", "tasks.md"):
                (feature / name).write_text(f"# {name}\n\nNo open markers.\n", encoding="utf-8")
            yield project_path

    def _g6(self, project_path: Path, workflow: str | None) -> tuple[int, dict[str, object]]:
        inputs: dict[str, object] = {"gate": "G6", "feature_dir": "specs/001-demo"}
        if workflow is not None:
            (project_path / "workflow.md").write_text(workflow, encoding="utf-8")
            inputs["workflow_file"] = "workflow.md"
        return self._helper_json("validate_gate", inputs, project_path)

    def test_validate_gate_g6_counts_open_workflow_analysis_rows(self) -> None:
        """#682: open HIGH rows in the workflow table fail G6 even when the planning files are clean."""
        if self.helper_filter and self.helper_filter != "validate-gate":
            self.skipTest("G6 workflow-table case uses validate-gate")
        open_rows = tuple((f"H{i}", "HIGH", f"required defect {i}", "") for i in range(3, 8))
        workflow = "\n".join(
            ("# Workflow", "", self.SEVERITY_LEGEND, "", "### Analysis Results", "", self.analysis_table(open_rows), "")
        )
        with self._g6_project() as project_path:
            code, payload = self._g6(project_path, workflow)
            self.assertEqual((1, False, 5), (code, payload["pass"], payload["markers"]))
            self.assertEqual({"critical": 0, "high": 5}, payload["analysis_findings"])
            self.assertEqual("5 CRITICAL/HIGH findings remain", payload["reason"])

    def test_validate_gate_g6_passes_once_every_resolution_cell_is_filled(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-gate":
            self.skipTest("G6 workflow-table case uses validate-gate")
        rows = (
            ("C1", "CRITICAL", "contract undefined", "Contract added to `contracts/api.md`."),
            ("H1", "HIGH", "cookie policy unspecified", "Policy stated in `plan.md`."),
            ("M1", "MEDIUM", "naming drift", ""),
            ("X1", "HIGH", "<!-- example row -->", "<!-- not a resolution -->"),
        )
        workflow = "\n".join(("# Workflow", "", "### Analysis Results", "", self.analysis_table(rows), ""))
        with self._g6_project() as project_path:
            code, payload = self._g6(project_path, workflow)
            self.assertEqual((1, False, 1), (code, payload["pass"], payload["markers"]))
            code, payload = self._g6(project_path, workflow.replace("<!-- not a resolution -->", "Fixed in `tasks.md`."))
            self.assertEqual((0, True, 0), (code, payload["pass"], payload["markers"]))
            self.assertEqual({"critical": 0, "high": 0}, payload["analysis_findings"])
            (project_path / "specs" / "001-demo" / "plan.md").write_text("- [HIGH] open marker\n", encoding="utf-8")
            code, payload = self._g6(project_path, workflow.replace("<!-- not a resolution -->", "Fixed."))
            self.assertEqual((1, False, 1), (code, payload["pass"], payload["markers"]))

    def test_validate_gate_g6_fails_closed_without_analysis_results_evidence(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-gate":
            self.skipTest("G6 workflow-table case uses validate-gate")
        commented_table = "\n".join(
            ("# Workflow", "", "<!--", "### Analysis Results", "", self.analysis_table((("H1", "HIGH", "x", "done"),)), "-->", "")
        )
        with self._g6_project() as project_path:
            for label, workflow in (
                ("no workflow_file", None),
                ("no table", "# Workflow\n\n" + self.SEVERITY_LEGEND + "\n"),
                ("commented-out table", commented_table),
            ):
                with self.subTest(case=label):
                    code, payload = self._g6(project_path, workflow)
                    self.assertEqual((1, False), (code, payload["pass"]))
                    self.assertNotIn("0 CRITICAL/HIGH", payload["reason"])
            code, payload = self._helper_json(
                "validate_gate",
                {"gate": "G6", "feature_dir": "specs/001-demo", "workflow_file": "missing-workflow.md"},
                project_path,
            )
            self.assertEqual((1, False), (code, payload["pass"]))

    def test_validate_gate_g6_workflow_path_is_canonicalized(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-gate":
            self.skipTest("G6 canonical workflow path case uses validate-gate")
        with self._g6_project() as project_path:
            (project_path / "docs").mkdir()
            (project_path / "workflow.md").write_text("# Workflow\n", encoding="utf-8")
            completed, response, _ = run_runner(
                helper_request(
                    "validate-gate",
                    {"gate": "G6", "feature_dir": "specs/001-demo", "workflow_file": "docs/../workflow.md"},
                ),
                cwd=project_path,
            )
            self.assertEqual(1, completed.returncode)
            payload = response["data"]["stdout_json"]
            self.assertFalse(payload["pass"])
            self.assertIn("workflow.md", payload["reason"])
            self.assertNotIn("..", payload["reason"])

    def test_estimate_reviewable_loc_does_not_pass_when_no_production_file_counts(self) -> None:
        if self.helper_filter and self.helper_filter != "estimate-reviewable-loc":
            self.skipTest("estimator stack cases use estimate-reviewable-loc")

        def estimate(project_path: Path, *entries: str) -> dict[str, object]:
            body = "\n".join(f"- NEW {entry}" for entry in entries)
            (project_path / "plan.md").write_text(f"# Plan\n\n## Declared File Operations\n\n{body}\n", encoding="utf-8")
            code, payload = self._helper_json("estimate_reviewable_loc", {"plan_file": "plan.md"}, project_path)
            self.assertEqual(0, code)
            return payload

        with helper_project() as project_path:
            payload = estimate(project_path, "docs/guide.md", "README.md")
            self.assertEqual("not_estimated", payload["status"])
            self.assertIsNone(payload["projected"])
            self.assertIn("no declared entry counted as production", payload["reason"])
            self.assertEqual(2, payload["declared_files"]["total_entries"])
            for label, entries, expected in (
                ("python package", ("mypkg/service.py", "tests/test_service.py"), 1),
                ("go layout", ("cmd/api/main.go", "internal/store/store.go", "internal/store/store_test.go"), 2),
                ("rust layout", ("crates/core/src/lib.rs", "crates/core/tests/it.rs"), 1),
                ("java layout", ("src/main/java/App.java", "service/src/main/kotlin/Api.kt"), 2),
            ):
                with self.subTest(layout=label):
                    payload = estimate(project_path, *entries)
                    self.assertEqual("pass", payload["status"])
                    self.assertEqual(expected, payload["declared_files"]["production"])

    def test_estimate_reviewable_loc_does_not_count_marker_evidence_toward_the_path_budget(self) -> None:
        if self.helper_filter and self.helper_filter != "estimate-reviewable-loc":
            self.skipTest("marker evidence case uses estimate-reviewable-loc")
        cap = 24
        entries = [f"src/module_{index:02d}.py" for index in range(4)]
        entries += [f"docs/page_{index:02d}.md" for index in range(cap - len(entries) - 1)]
        entries.append("specs/001-demo/.process/reviewability/us1.json")
        evidence = [
            "specs/001-demo/.process/checkpoints/us1.json",
            "specs/001-demo/.process/verification/us1.json",
        ]
        body = "\n".join(f"- NEW {entry}" for entry in entries + evidence)
        with helper_project() as project_path:
            (project_path / "plan.md").write_text(
                f"# Plan\n\n## Declared File Operations\n\n{body}\n", encoding="utf-8"
            )
            code, payload = self._helper_json(
                "estimate_reviewable_loc", {"plan_file": "plan.md"}, project_path
            )
        self.assertEqual(0, code)
        declared = payload["declared_files"]
        self.assertEqual(cap, declared["total_entries"])
        self.assertEqual(cap, declared["new"])
        self.assertEqual(4, declared["production"])
        self.assertEqual(len(evidence), declared["marker_evidence"])

    def test_estimate_reviewable_loc_does_not_count_the_implementation_notes_record(self) -> None:
        """#801: the notes record is committed run evidence, like a marker's records, not budgeted work."""
        if self.helper_filter and self.helper_filter != "estimate-reviewable-loc":
            self.skipTest("implementation notes case uses estimate-reviewable-loc")
        cap = 24
        entries = [f"src/module_{index:02d}.py" for index in range(4)]
        entries += [f"docs/page_{index:02d}.md" for index in range(cap - len(entries))]
        notes = "specs/001-demo/.process/implementation-notes.md"
        body = "\n".join(f"- NEW {entry}" for entry in [*entries, notes])
        with helper_project() as project_path:
            (project_path / "plan.md").write_text(
                f"# Plan\n\n## Declared File Operations\n\n{body}\n", encoding="utf-8"
            )
            code, payload = self._helper_json(
                "estimate_reviewable_loc", {"plan_file": "plan.md"}, project_path
            )
        self.assertEqual(0, code)
        declared = payload["declared_files"]
        self.assertEqual(cap, declared["total_entries"])
        self.assertEqual(1, declared["implementation_notes"])
        self.assertEqual(0, declared["marker_evidence"])

    def test_detect_commands_finds_repository_test_runner(self) -> None:
        """A runner script under tests/ is real, verifiable evidence of a test command.

        A repository can be pure-stdlib Python with no packaging marker at all;
        returning every command as N/A there reads as "this project has no
        tests" rather than "the detector stopped at the repository root".
        """
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("test-runner discovery case uses detect-commands")
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
            project_path = Path(project).resolve()
            (project_path / "tests" / "suite").mkdir(parents=True)
            (project_path / "tests" / "suite" / "run-all.py").write_text("", encoding="utf-8")
            payload = self._detected(project_path)
            self.assertEqual("python", payload["stack"])
            self.assertEqual("python3 tests/suite/run-all.py", payload["commands"]["UNIT_TEST"])
            self.assertEqual("python3 tests/suite/run-all.py", payload["commands"]["FULL_VERIFY"])
            self.assertEqual("test_runner_script", payload["detection"]["source"])
            self.assertEqual("tests/suite/run-all.py", payload["detection"]["evidence"])

    def test_detect_commands_recognizes_python_without_pyproject(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("python marker case uses detect-commands")
        for marker in ("requirements.txt", "setup.py", "setup.cfg", "tox.ini", "pytest.ini", "Pipfile"):
            with self.subTest(marker=marker):
                with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
                    project_path = Path(project).resolve()
                    (project_path / marker).write_text("", encoding="utf-8")
                    payload = self._detected(project_path)
                    self.assertEqual("python", payload["stack"])
                    self.assertEqual("pytest", payload["commands"]["UNIT_TEST"])
                    self.assertEqual(marker, payload["detection"]["evidence"])

    def test_detect_commands_prefers_root_marker_over_runner_script(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("precedence case uses detect-commands")
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
            project_path = Path(project).resolve()
            (project_path / "pyproject.toml").write_text("", encoding="utf-8")
            (project_path / "tests" / "suite").mkdir(parents=True)
            (project_path / "tests" / "suite" / "run-all.py").write_text("", encoding="utf-8")
            payload = self._detected(project_path)
            self.assertEqual("pytest", payload["commands"]["UNIT_TEST"])
            self.assertEqual("root_marker", payload["detection"]["source"])

    def test_detect_commands_fills_quality_gate_slots_from_discovery_table(self) -> None:
        """The three quality-gate slots come from the shipped table, keyed on signal files."""
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("gate slot case uses detect-commands")
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
            project_path = Path(project).resolve()
            (project_path / "pyproject.toml").write_text("", encoding="utf-8")
            (project_path / ".importlinter").write_text("", encoding="utf-8")
            payload = self._detected(project_path)
            self.assertEqual("lint-imports --config .importlinter", payload["commands"]["DEPENDENCY_RULES"])
            self.assertIn("{plugin_root}/scripts/crap-score.py", payload["commands"]["COMPLEXITY"])
            self.assertIn("{paths}", payload["commands"]["COMPLEXITY"])
            self.assertEqual("N/A", payload["commands"]["MUTATION"])
            self.assertEqual("populated", payload["gates"]["DEPENDENCY_RULES"]["status"])
            self.assertEqual("import-linter", payload["gates"]["DEPENDENCY_RULES"]["tool"])
            self.assertIn(payload["gates"]["DEPENDENCY_RULES"]["tool_present"], (True, False))
            self.assertEqual("unconfigured", payload["gates"]["MUTATION"]["status"])
            self.assertTrue(payload["plugin_root"])
            self.assertEqual("missing", payload["quality_gates"]["status"])
            self.assertEqual(".specify/quality-gates.json", payload["quality_gates"]["path"])
            (project_path / ".specify").mkdir()
            (project_path / ".specify" / "quality-gates.json").write_text(
                '{"schema_version":"1.0","thresholds":{"complexity":5,"crap":12,"mutation_score_floor":70},'
                '"skips":{"DEPENDENCY_RULES":{"reason":"single module"}}}',
                encoding="utf-8",
            )
            payload = self._detected(project_path)
            self.assertEqual("present", payload["quality_gates"]["status"])
            self.assertIn("--ceiling 12 --complexity-ceiling 5", payload["commands"]["COMPLEXITY"])
            self.assertEqual("skipped", payload["gates"]["DEPENDENCY_RULES"]["status"])
            self.assertEqual("N/A", payload["commands"]["DEPENDENCY_RULES"])
            (project_path / ".specify" / "quality-gates.json").write_text('{"schema_version":"1.0"}', encoding="utf-8")
            payload = self._detected(project_path)
            self.assertEqual("invalid", payload["quality_gates"]["status"])
            self.assertTrue(payload["quality_gates"]["problems"])
            self.assertIn("--ceiling 30 --complexity-ceiling 10", payload["commands"]["COMPLEXITY"])
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
            payload = self._detected(Path(project).resolve())
            self.assertEqual({"N/A"}, {payload["commands"][slot] for slot in ("COMPLEXITY", "MUTATION", "DEPENDENCY_RULES")})

    def test_detect_commands_fills_lint_and_typecheck_only_on_a_tool_signal(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("lint default case uses detect-commands")
        cases = (
            ("no python signal", {"pyproject.toml": "[project]\nname = 'x'\n"}, "N/A", "N/A"),
            ("ruff.toml", {"pyproject.toml": "", "ruff.toml": ""}, "ruff check", "N/A"),
            ("tool.ruff and tool.mypy", {"pyproject.toml": "[tool.ruff]\nline-length = 100\n[tool.mypy]\nstrict = true\n"}, "ruff check", "mypy ."),
            ("ruff dev dependency", {"pyproject.toml": "[dependency-groups]\ndev = [\"ruff>=0.6\"]\n"}, "ruff check", "N/A"),
            ("requirements pin", {"requirements-dev.txt": "ruff==0.6.0\n", "requirements.txt": ""}, "ruff check", "N/A"),
            ("mypy.ini", {"setup.py": "", "mypy.ini": "[mypy]\n"}, "N/A", "mypy ."),
            ("setup.cfg mypy section", {"setup.cfg": "[mypy]\nstrict = True\n"}, "N/A", "mypy ."),
            ("go", {"go.mod": "module x\n"}, "go vet ./...", "N/A"),
            ("rust", {"Cargo.toml": "[package]\n"}, "cargo clippy -- -D warnings", "N/A"),
        )
        for label, files, lint, typecheck in cases:
            with self.subTest(case=label):
                with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
                    project_path = Path(project).resolve()
                    for name, text in files.items():
                        (project_path / name).write_text(text, encoding="utf-8")
                    payload = self._detected(project_path)
                    self.assertEqual((lint, typecheck), (payload["commands"]["LINT"], payload["commands"]["TYPECHECK"]))
                    if lint != "N/A":
                        self.assertIn(lint, payload["commands"]["FULL_VERIFY"])

    def test_detect_commands_reports_the_base_branch_for_the_mutation_filter(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("base branch case uses detect-commands")
        git_env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

        def git(project_path: Path, *args: str) -> None:
            subprocess.run(["git", "-C", str(project_path), *args], check=True, capture_output=True, env=git_env)

        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
            project_path = Path(project).resolve()
            (project_path / "pyproject.toml").write_text("", encoding="utf-8")
            (project_path / "cosmic-ray.toml").write_text("", encoding="utf-8")
            payload = self._detected(project_path)
            self.assertEqual({"value": "origin/main", "source": "default"}, payload["base_branch"])
            git(project_path, "init", "-q", "-b", "trunk")
            git(project_path, "-c", "user.email=native-eval@example.invalid", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "i")
            git(project_path, "update-ref", "refs/remotes/origin/trunk", "HEAD")
            git(project_path, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
            payload = self._detected(project_path)
            self.assertEqual({"value": "origin/trunk", "source": "origin_head"}, payload["base_branch"])
            self.assertIn("'origin/trunk' | cr-filter-git --config -", payload["commands"]["MUTATION"])

    def test_detect_commands_runs_the_dependency_audit_only_on_opt_in(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("dependency audit case uses detect-commands")
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
            project_path = Path(project).resolve()
            (project_path / "package.json").write_text("{}", encoding="utf-8")
            (project_path / "package-lock.json").write_text("{}", encoding="utf-8")
            payload = self._detected(project_path)
            self.assertEqual("off", payload["gates"]["DEPENDENCY_AUDIT"]["status"])
            self.assertEqual("N/A", payload["commands"]["DEPENDENCY_AUDIT"])
            (project_path / ".specify").mkdir()
            (project_path / ".specify" / "quality-gates.json").write_text(
                '{"schema_version":"1.0","thresholds":{"complexity":5,"crap":12,"mutation_score_floor":70},'
                '"enforce":["DEPENDENCY_AUDIT"]}',
                encoding="utf-8",
            )
            payload = self._detected(project_path)
            self.assertEqual(["DEPENDENCY_AUDIT"], payload["quality_gates"]["enforce"])
            self.assertEqual("populated", payload["gates"]["DEPENDENCY_AUDIT"]["status"])
            self.assertEqual(
                'env -i PATH="$PATH" HOME="$HOME" npm_config_userconfig=/dev/null '
                "npm audit --audit-level=high --registry=https://registry.npmjs.org/",
                payload["commands"]["DEPENDENCY_AUDIT"],
            )

    def test_detect_commands_runner_discovery_is_deterministic(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("determinism case uses detect-commands")
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
            project_path = Path(project).resolve()
            for sub in ("zeta", "alpha"):
                (project_path / "tests" / sub).mkdir(parents=True)
                (project_path / "tests" / sub / "run-all.py").write_text("", encoding="utf-8")
            first = self._detected(project_path)["commands"]["UNIT_TEST"]
            self.assertEqual("python3 tests/alpha/run-all.py", first)
            for _ in range(3):
                self.assertEqual(first, self._detected(project_path)["commands"]["UNIT_TEST"])

    def test_detect_commands_reports_what_it_searched_when_nothing_found(self) -> None:
        """An empty result must say it looked, not just return a wall of N/A."""
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("no-detection case uses detect-commands")
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
            payload = self._detected(Path(project).resolve())
            self.assertEqual("unknown", payload["stack"])
            self.assertEqual("none", payload["detection"]["source"])
            self.assertEqual("", payload["detection"]["evidence"])
            searched = payload["detection"]["searched"]
            self.assertIn("pyproject.toml", searched)
            self.assertIn("package.json", searched)
            self.assertTrue(payload["detection"]["hint"])

    def test_trusted_text_returns_none_on_read_error(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("trusted text read-error case uses shared helper behavior")
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
            path = Path(project).resolve() / "unreadable.md"
            path.write_text("secret\n", encoding="utf-8")
            from speckit_pro_runner.helpers import read_only

            with patch.object(read_only.os, "open", side_effect=PermissionError("denied")) as denied_open:
                self.assertIsNone(read_only.trusted_text(path, path.parent))
                denied_open.assert_called_once()

    @unittest.skipIf(os.name == "nt", "POSIX no-follow descriptor behavior is not portable to Windows")
    def test_trusted_bytes_rejects_symlink_replacement_between_check_and_open(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("trusted bytes race case uses shared helper behavior")
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project, tempfile.TemporaryDirectory() as outside:
            project_path = Path(project).resolve()
            target = project_path / "packet.json"
            target.write_text('{"packet": true}\n', encoding="utf-8")
            outside_file = Path(outside) / "outside.json"
            outside_file.write_text('{"outside": true}\n', encoding="utf-8")
            from speckit_pro_runner.helpers import read_only

            real_open = read_only.os.open
            swapped = False

            def swap_before_leaf_open(path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None):
                nonlocal swapped
                if path == "packet.json" and dir_fd is not None and not swapped:
                    target.unlink()
                    target.symlink_to(outside_file)
                    swapped = True
                return real_open(path, flags, mode, dir_fd=dir_fd)

            with patch.object(read_only.os, "open", side_effect=swap_before_leaf_open):
                self.assertIsNone(read_only.trusted_bytes(target, project_path))
            self.assertTrue(swapped)

    def test_git_branch_rejects_symlinked_git_paths(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git branch symlink case uses check-prerequisites")
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project, tempfile.TemporaryDirectory() as outside:
            project_path = Path(project).resolve()
            outside_git = Path(outside) / "gitfile"
            outside_git.write_text("gitdir: /tmp/outside\n", encoding="utf-8")
            try:
                (project_path / ".git").symlink_to(outside_git)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "")

    def test_git_branch_reports_head_for_detached_checkout(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git branch detached-HEAD case uses check-prerequisites")
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
            project_path = Path(project).resolve()
            git_dir = project_path / ".git"
            git_dir.mkdir()
            (git_dir / "HEAD").write_text("2d7388cc96f81cb805948bc19a8ccdd1cf896222\n", encoding="utf-8")
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "HEAD")

    def test_git_branch_rejects_symlinked_head_escape(self) -> None:
        if self.helper_filter and self.helper_filter != "check-prerequisites":
            self.skipTest("git HEAD symlink case uses check-prerequisites")
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project, tempfile.TemporaryDirectory() as outside:
            project_path = Path(project).resolve()
            git_dir = project_path / ".git"
            git_dir.mkdir()
            outside_head = Path(outside) / "HEAD"
            outside_head.write_text("ref: refs/heads/external\n", encoding="utf-8")
            try:
                (git_dir / "HEAD").symlink_to(outside_head)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            from speckit_pro_runner.helpers.read_only import git_branch

            self.assertEqual(git_branch(project_path), "")

    def test_repo_root_for_specs_path_uses_rightmost_specs_segment(self) -> None:
        if self.helper_filter and self.helper_filter != "o5-topology":
            self.skipTest("spec root inference case uses o5-topology")
        with tempfile.TemporaryDirectory(prefix="read-only-helper-project-") as project:
            project_path = Path(project).resolve()
            target = project_path / "outer" / "specs" / "container" / "repo" / "specs" / "feature"
            expected = project_path / "outer" / "specs" / "container" / "repo"
            from speckit_pro_runner.helpers.read_only import repo_root_for_specs_path

            self.assertEqual(repo_root_for_specs_path(target, project_path), expected.resolve(strict=False))

    def test_runtime_info_smoke_fixture_still_works(self) -> None:
        if self.helper_filter and self.helper_filter != "helper-registry-dispatch":
            self.skipTest("runtime smoke is registry-level")
        request = json.loads((FIXTURE_DIR / "smoke-runtime-info-request.json").read_text(encoding="utf-8"))
        completed, response, stderr_records = run_runner(request)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(stderr_records, [])
        self.assert_response(response, "ok", 0)
        self.assertEqual(response["data"]["report"]["runner_contract_id"], "speckit-pro-runner")

    def test_claude_subagent_runtime_resolves_versioned_capabilities(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-claude-subagent-runtime":
            self.skipTest("Claude runtime cases use resolve-claude-subagent-runtime")

        from speckit_pro_runner.helpers.read_only import resolve_claude_subagent_runtime

        modern = resolve_claude_subagent_runtime(
            {
                "client_version": "2.1.251 (Claude Code)",
                "execution_mode": "interactive",
                "agent_teams_env_enabled": True,
                "team_contract_verified": True,
                "auto_memory_enabled": True,
            },
            REPO_ROOT,
        )
        self.assertEqual(modern["exit_code"], 0)
        record = json.loads(modern["stdout"])
        self.assertEqual(record["client_version"], "2.1.251")
        self.assertEqual(record["concurrency"], {"limit": 20, "wave_size": 19, "source": "client_default"})
        self.assertEqual(record["spawn_depth"], {"limit": 3, "source": "client_default"})
        self.assertTrue(record["partial_resume"]["supported"])
        self.assertEqual(record["partial_resume"]["strategy"], "same_agent_once")
        self.assertTrue(record["native_fallback"]["supported"])
        self.assertTrue(record["cache_ttl"]["client_supported"])
        self.assertFalse(record["cache_ttl"]["plugin_agent_supported"])
        self.assertFalse(record["cache_ttl"]["adopted"])
        self.assertTrue(record["agent_teams"]["available"])
        self.assertTrue(record["auto_memory"]["enabled"])

        low_cap = resolve_claude_subagent_runtime(
            {
                "client_version": "2.1.251",
                "execution_mode": "headless",
                "max_concurrent_subagents": "2",
                "max_subagent_spawn_depth": "4",
                "agent_teams_env_enabled": True,
                "team_contract_verified": True,
                "auto_memory_enabled": False,
            },
            REPO_ROOT,
        )
        record = json.loads(low_cap["stdout"])
        self.assertEqual(record["concurrency"], {"limit": 2, "wave_size": 1, "source": "environment_override"})
        self.assertEqual(record["spawn_depth"], {"limit": 4, "source": "environment_override"})
        self.assertFalse(record["agent_teams"]["available"])
        self.assertIn("headless", record["agent_teams"]["reason"])

        legacy = resolve_claude_subagent_runtime(
            {"client_version": "2.1.216", "execution_mode": "interactive"},
            REPO_ROOT,
        )
        record = json.loads(legacy["stdout"])
        self.assertEqual(record["concurrency"], {"limit": 5, "wave_size": 4, "source": "compatibility_default"})
        self.assertEqual(record["spawn_depth"], {"limit": 1, "source": "compatibility_default"})
        self.assertFalse(record["partial_resume"]["supported"])
        self.assertEqual(record["partial_resume"]["strategy"], "fresh_retry_once")
        self.assertFalse(record["native_fallback"]["supported"])
        self.assertFalse(record["cache_ttl"]["client_supported"])
        self.assertFalse(record["auto_memory"]["enabled"])

        numeric_override = resolve_claude_subagent_runtime(
            {
                "client_version": "2.1.251",
                "execution_mode": "interactive",
                "max_concurrent_subagents": 3,
                "max_subagent_spawn_depth": 2,
            },
            REPO_ROOT,
        )
        record = json.loads(numeric_override["stdout"])
        self.assertEqual(record["concurrency"], {"limit": 3, "wave_size": 2, "source": "environment_override"})
        self.assertEqual(record["spawn_depth"], {"limit": 2, "source": "environment_override"})

        invalid_override = resolve_claude_subagent_runtime(
            {
                "client_version": "2.1.251",
                "execution_mode": "interactive",
                "max_concurrent_subagents": "zero",
            },
            REPO_ROOT,
        )
        record = json.loads(invalid_override["stdout"])
        self.assertEqual(record["concurrency"], {"limit": 1, "wave_size": 1, "source": "invalid_environment_override"})
        self.assertTrue(any("MAX_CONCURRENT_SUBAGENTS" in warning for warning in record["warnings"]))

        boolean_override = resolve_claude_subagent_runtime(
            {
                "client_version": "2.1.251",
                "execution_mode": "interactive",
                "max_concurrent_subagents": True,
            },
            REPO_ROOT,
        )
        record = json.loads(boolean_override["stdout"])
        self.assertEqual(record["concurrency"], {"limit": 1, "wave_size": 1, "source": "invalid_environment_override"})

    def test_claude_subagent_runtime_rejects_unknown_execution_mode(self) -> None:
        if self.helper_filter and self.helper_filter != "resolve-claude-subagent-runtime":
            self.skipTest("Claude runtime cases use resolve-claude-subagent-runtime")

        from speckit_pro_runner.helpers.read_only import resolve_claude_subagent_runtime

        result = resolve_claude_subagent_runtime(
            {"client_version": "2.1.251", "execution_mode": "daemon"},
            REPO_ROOT,
        )
        self.assertEqual(result["exit_code"], 2)
        self.assertEqual(
            json.loads(result["stdout"])["error"],
            "execution_mode must be interactive or headless",
        )

    def test_promoted_helper_runs_without_bash_on_path(self) -> None:
        if self.helper_filter and self.helper_filter != "detect-commands":
            self.skipTest("no-Bash smoke is scoped to detect-commands")
        with helper_project() as project_path:
            (project_path / "pnpm-lock.yaml").write_text("", encoding="utf-8")
            (project_path / "package.json").write_text(
                '{"scripts":{"build":"tsup","test":"vitest run"}}\n',
                encoding="utf-8",
            )
            completed, response, stderr_records = run_runner(
                helper_request("detect-commands", {"repo_root": "."}),
                extra_env={"PATH": "/nonexistent"},
                cwd=project_path,
            )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        self.assertEqual(response["data"]["stdout_json"]["stack"], "nodejs")
        self.assertEqual(stderr_records, [])

    def test_count_markers_modes_match_bash_reference(self) -> None:
        if self.helper_filter and self.helper_filter != "count-markers":
            self.skipTest("count-markers expanded parity cases")
        for marker_type in ("gaps", "findings", "clarifications", "all"):
            with self.subTest(marker_type=marker_type):
                self.assert_helper_matches_bash_reference(
                    "count-markers",
                    {"type": marker_type, "feature_dir": FEATURE_DIR},
                )

    def test_validate_gate_modes_match_bash_reference(self) -> None:
        if self.helper_filter and self.helper_filter != "validate-gate":
            self.skipTest("validate-gate expanded parity cases")
        for gate in ("G1", "G2", "G3", "G4", "G5", "G6", "G7"):
            with self.subTest(gate=gate):
                self.assert_helper_matches_bash_reference(
                    "validate-gate",
                    {"gate": gate, "feature_dir": FEATURE_DIR},
                )

    def test_plan_layers_valid_real_preserves_legacy_increment_contract(self) -> None:
        if self.helper_filter and self.helper_filter != "plan-layers-feature-dir":
            self.skipTest("plan-layers valid fixture case")
        completed, response, planner = self.run_plan_layers(f"{PLAN_LAYERS_FIXTURE_DIR}/valid-real")
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        self.assertEqual(planner["status"], "ok")
        self.assertEqual(planner["summary"]["increment_count"], 4)
        self.assertEqual(planner["summary"]["task_count"], 8)
        increments = planner["increments"]
        self.assertEqual([increment["id"] for increment in increments], ["foundation", "us1", "us2", "polish"])
        self.assertEqual([increment["order"] for increment in increments], [0, 1, 2, 3])
        self.assertEqual(
            [increment["depends_on"] for increment in increments],
            [[], ["foundation"], ["us1"], ["us2"]],
        )
        tasks = {task["id"]: task for increment in increments for task in increment["tasks"]}
        self.assertEqual(len(tasks), 8)
        self.assertEqual(tasks["T003"]["status"], "done")
        self.assertTrue(tasks["T004"]["parallel"])
        self.assertEqual(tasks["T004"]["story"], "us1")
        self.assertEqual(tasks["T004"]["increment_id"], "us1")

    def test_plan_layers_dependency_cycle_is_invalid_plan(self) -> None:
        if self.helper_filter and self.helper_filter != "plan-layers-feature-dir":
            self.skipTest("plan-layers dependency-cycle case")
        completed, response, planner = self.run_plan_layers(f"{PLAN_LAYERS_FIXTURE_DIR}/dependency-cycle")
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        self.assertEqual(planner["status"], "invalid_plan")
        cycle_errors = [error for error in planner["errors"] if error["code"] == "dependency_cycle"]
        self.assertEqual(len(cycle_errors), 1)
        self.assertEqual(cycle_errors[0]["details"]["cycle"], ["us1", "us2", "us3", "us1"])

    def test_plan_layers_malformed_task_is_invalid_plan(self) -> None:
        if self.helper_filter and self.helper_filter != "plan-layers-feature-dir":
            self.skipTest("plan-layers malformed-task case")
        completed, response, planner = self.run_plan_layers(f"{PLAN_LAYERS_FIXTURE_DIR}/malformed-task")
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure", 1)
        self.assertEqual(planner["status"], "invalid_plan")
        self.assertEqual(
            {error["code"] for error in planner["errors"]},
            {"duplicate_task_id", "duplicate_increment_id", "malformed_task"},
        )

    def test_plan_layers_repository_bash_confinement_preserves_increment_contract(self) -> None:
        if self.helper_filter and self.helper_filter != "plan-layers-feature-dir":
            self.skipTest("plan-layers repository Bash confinement case")
        completed, response, stderr_records = run_runner(
            helper_request(
                "plan-layers-feature-dir",
                {"feature_dir": REPOSITORY_BASH_CONFINEMENT_PLAN_DIR},
            )
        )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok", 0)
        self.assertEqual(stderr_records, [])
        data = response["data"]
        stdout = data["stdout"]
        self.assertFalse(stdout["truncated"])
        self.assertEqual(stdout["limit_bytes"], PLAN_LAYERS_CAPTURE_LIMIT_BYTES)
        self.assertLessEqual(stdout["byte_count"], stdout["limit_bytes"])
        self.assertIn("stdout_json", data)
        planner = data["stdout_json"]
        self.assertEqual(planner["status"], "ok")
        self.assertEqual(planner["summary"]["increment_count"], 18)
        self.assertEqual(planner["summary"]["task_count"], 136)
        self.assertEqual(
            [increment["id"] for increment in planner["increments"]],
            ["foundation", "us1", "us16", *[f"us{number}" for number in range(2, 16)], "polish"],
        )
        self.assertEqual(planner["increments"][0]["depends_on"], [])
        self.assertEqual(planner["increments"][1]["depends_on"], ["foundation"])
        self.assertEqual(planner["increments"][2]["depends_on"], ["us1"])

    def test_helper_python_authoritative_records(self) -> None:
        for helper_id in self.filtered_helpers():
            if helper_id in {"helper-registry-dispatch", "scaffold-answers", "g0-setup", "probe-git-write", "phase-brief"}:
                continue
            with self.subTest(helper_id=helper_id):
                completed, response, stderr_records = run_runner(helper_request(helper_id, HELPER_CASES[helper_id]))
                data = response["data"]
                if helper_id in {"formal-doctor", "select-artifact-pages"}:
                    self.assertEqual(completed.returncode, 0)
                    field, expected = {
                        "formal-doctor": ("verdict", "disabled"),
                        "select-artifact-pages": ("selected_pages", ["implementation-plan", "spec-explainer", "module-map"]),
                    }[helper_id]
                    self.assertEqual(data[field], expected)
                    self.assertFalse(data["writes_state"])
                    self.assertEqual(stderr_records, [])
                    continue
                if helper_id == "research-broker-preflight":
                    # Rerun against an empty temporary HOME so the real
                    # machine's binary and key files never decide the result.
                    with tempfile.TemporaryDirectory(prefix="research-preflight-home-") as home:
                        completed, response, stderr_records = run_runner(
                            helper_request(helper_id, HELPER_CASES[helper_id]),
                            extra_env={
                                "HOME": home,
                                "EVALUATE_BIN": "",
                                "JEV_API_KEY_FILE": "",
                                "JEV_FALLBACK_API_KEY_FILE": "",
                                "TYPESAFE_API_KEY": "",
                                "OPENROUTER_API_KEY": "",
                                "TAVILY_API_KEY": "",
                                "CONTEXT7_API_KEY": "",
                            },
                        )
                    data = response["data"]
                    self.assert_response(response, "ok", 0)
                    self.assertEqual(data["jev"]["state"], "binary_missing")
                    self.assertEqual(data["screening_mode"], "sanitizer-only")
                    self.assertFalse(data["writes_state"])
                    self.assertEqual(stderr_records, [])
                    continue
                if helper_id == "render-egress-authorization":
                    self.assert_response(response, "ok", 0)
                    self.assertFalse(data["writes_state"])
                    self.assertEqual(data["action_ids"], ["live-skill-eval", "push-feature-branch"])
                    self.assertIn("[auto_review]\nextra_policy = ", data["extra_policy_fragment"])
                    self.assertEqual(stderr_records, [])
                    continue
                if helper_id == "check-gate-preflight-coverage":
                    self.assert_response(response, "ok", 0)
                    self.assertFalse(data["writes_state"])
                    self.assertTrue(data["covered"])
                    self.assertEqual(stderr_records, [])
                    continue
                if helper_id == "finalize-run":
                    self.assert_response(response, "ok", 0)
                    self.assertFalse(data["writes_state"])
                    # The fixture deferral failed every escalation tier: the run finalizes ready for review.
                    self.assertEqual((data["outcome"], data["ready_commands"], [d["class"] for d in data["decisions"]]),
                                     ("complete_with_deferred", ["gh pr ready 101", "gh pr ready 102"], ["exhausted"]))
                    self.assertEqual(stderr_records, [])
                    continue
                if helper_id == "ratify-pr-split":
                    self.assert_response(response, "ok", 0)
                    self.assertFalse(data["writes_state"])
                    self.assertEqual(data["decision"], "autopilot_ratified")
                    self.assertEqual(data["ratified_by"], "autopilot")
                    self.assertEqual(stderr_records, [])
                    continue
                if helper_id == "check-roadmap-freshness":
                    # A throwaway repository with no remote: the roadmap cannot be
                    # verified, so the helper stops instead of passing.
                    with tempfile.TemporaryDirectory(prefix="roadmap-freshness-repo-") as repo:
                        root = Path(repo)
                        (root / ".specify").mkdir()
                        (root / "docs/ai").mkdir(parents=True)
                        (root / "docs/ai/technical-roadmap.md").write_text("# roadmap\n", encoding="utf-8")
                        completed, response, stderr_records = run_runner(
                            helper_request(helper_id, HELPER_CASES[helper_id]),
                            cwd=root,
                        )
                    data = response["data"]
                    self.assert_response(response, "expected_failure", 1)
                    self.assertFalse(data["writes_state"])
                    self.assertEqual((data["verdict"], data["cause"]), ("stop", "no_remote"))
                    continue
                if helper_id == "list-archive-candidates":
                    # A throwaway repository with no gh on PATH: the prior spec
                    # has no readable merge evidence, so it stays active.
                    with tempfile.TemporaryDirectory(prefix="archive-sweep-repo-") as repo:
                        root = Path(repo)
                        (root / ".specify").mkdir()
                        for name in ("000-prior-feature", "001-current-feature"):
                            (root / "specs" / name).mkdir(parents=True)
                            (root / "specs" / name / "spec.md").write_text("# spec\n", encoding="utf-8")
                        completed, response, stderr_records = run_runner(
                            helper_request(helper_id, HELPER_CASES[helper_id]),
                            extra_env={"PATH": str(root / "empty-path")},
                            cwd=root,
                        )
                    data = response["data"]
                    self.assert_response(response, "ok", 0)
                    self.assertEqual(stderr_records, [])
                    self.assertFalse(data["writes_state"])
                    self.assertEqual(data["excluded_current_spec"], "specs/001-current-feature")
                    self.assertEqual(data["archive_order"], [])
                    self.assertEqual(data["unknown"], ["specs/000-prior-feature"])
                    continue
                self.assertEqual(data["shell"], False)
                self.assertEqual(data["argv"][-2:], ["-m", "speckit_pro_runner"])
                self.assertEqual(data["python_operation"], helper_id)
                self.assertTrue(data["authoritative_command"].endswith("| python -m speckit_pro_runner"))
                expected_stdout_limit = (
                    PLAN_LAYERS_CAPTURE_LIMIT_BYTES
                    if helper_id in {"plan-layers-feature-dir", "render-plan-repair-context"}
                    else GENERIC_CAPTURE_LIMIT_BYTES
                )
                self.assertEqual(data["stdout"]["limit_bytes"], expected_stdout_limit)
                self.assertEqual(data["stderr"]["limit_bytes"], GENERIC_CAPTURE_LIMIT_BYTES)
                self.assertEqual(completed.returncode, response["exit_code"])
                self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])
                expected_status = {0: "ok", 1: "expected_failure", 2: "input_error", 3: "missing_prerequisite"}.get(data["exit_code"], "subprocess_failure")
                if helper_id == "confidence-gate" and data.get("stdout_json", {}).get("recommended_action") == "soft_skip":
                    expected_status = "ok"
                expected_code = {"ok": 0, "expected_failure": 1, "input_error": 2, "missing_prerequisite": 3}.get(expected_status, response["exit_code"])
                self.assert_response(response, expected_status, expected_code)


class PlanLayersRepairRouteTests(_ReadOnlyHelperRunner, unittest.TestCase):
    """A plan-layers failure routes its repair to the agent that owns the fix."""

    def test_plan_layers_invalid_plan_routes_tasks_md_repair_to_the_phase_executor(self) -> None:
        if self.helper_filter and self.helper_filter != "plan-layers-feature-dir":
            self.skipTest("plan-layers repair route case")
        _, _, planner = self.run_plan_layers(f"{PLAN_LAYERS_FIXTURE_DIR}/dependency-cycle")
        self.assertEqual(planner["status"], "invalid_plan")
        repair = planner["repair"]
        self.assertEqual(repair["owner"], "phase-executor")
        self.assertEqual(repair["target"], f"{PLAN_LAYERS_FIXTURE_DIR}/dependency-cycle/tasks.md")
        self.assertEqual(repair["retry"], "plan-layers-feature-dir")
        self.assertNotIn("repair", self.run_plan_layers(f"{PLAN_LAYERS_FIXTURE_DIR}/valid-real")[2])

    def test_plan_layers_input_error_routes_by_what_is_missing(self) -> None:
        if self.helper_filter and self.helper_filter != "plan-layers-feature-dir":
            self.skipTest("plan-layers input-error repair route case")
        cases = (
            (PLAN_LAYERS_FIXTURE_DIR, "tasks_file_missing", "phase-executor"),
            (f"{PLAN_LAYERS_FIXTURE_DIR}/no-such-feature", "feature_dir_not_found", "orchestrator"),
        )
        for feature_dir, code, owner in cases:
            with self.subTest(code=code):
                completed, response, planner = self.run_plan_layers(feature_dir)
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(planner["status"], "input_error")
                self.assertEqual(planner["errors"][0]["code"], code)
                self.assertEqual(planner["repair"]["owner"], owner)
                self.assertEqual(planner["repair"]["retry"], "plan-layers-feature-dir")


class PacketTitlePatternTests(unittest.TestCase):
    """The packet schema and the live PR-title gate accept the same title scopes."""

    def test_pr_packet_schema_and_title_gate_accept_the_same_scopes(self) -> None:
        schema = json.loads(PR_PACKET_SCHEMA.read_text(encoding="utf-8"))
        title_properties = schema["$defs"]["generated_title"]["properties"]
        scope_pattern = title_properties["scope"]["pattern"]
        value_pattern = title_properties["value"]["pattern"]
        self.assertEqual(scope_pattern, PACKET_TITLE_SCOPE_PATTERN)
        self.assertEqual(value_pattern, PACKET_TITLE_VALUE_PATTERN)

        for scope in ("speckit-pro", "feature-001", "spec-014c"):
            with self.subTest(scope=scope, expected="accepted"):
                title = f"feat({scope}): Add packet validation"
                self.assertIsNotNone(re.fullmatch(scope_pattern, scope))
                self.assertIsNotNone(re.fullmatch(value_pattern, title))
                self.assertEqual(self.title_gate_status(title), "ok")

        for scope in ("FEATURE-001", "FIXTURE-014C", "PRsg-012", "SPEC-014c", "speckit-PRO"):
            with self.subTest(scope=scope, expected="rejected"):
                title = f"feat({scope}): Add packet validation"
                self.assertIsNone(re.fullmatch(scope_pattern, scope))
                self.assertIsNone(re.fullmatch(value_pattern, title))
                self.assertEqual(self.title_gate_status(title), "expected_failure")

    @staticmethod
    def title_gate_status(title: str) -> str:
        """The status the live PR-title gate reports for `title`."""
        request = REPO_ROOT / "tests" / "speckit-pro" / "unit" / "fixtures" / "runner-gates" / "requests" / "validate-pr-title-live.json"
        completed = subprocess.run(
            [sys.executable, "-m", "speckit_pro_runner"], input=request.read_text(encoding="utf-8"), text=True, capture_output=True,
            cwd=REPO_ROOT, check=False, env={**os.environ, "TITLE": title, "PYTHONPATH": str(PLUGIN_ROOT)},
        )
        return str(json.loads(completed.stdout)["status"])


PLAN_LAYERS_FILES = ("src/contract.md", "src/planner.py", "tests/test_planner.py")
PLAN_LAYERS_BASELINE = {
    "foundation": "- [ ] T001 Prepare the contract in src/contract.md",
    "story": "- [ ] T002 [US1] Build the planner in src/planner.py and tests/test_planner.py",
    "extra_phase": "",
    "notes": "",
    "us1_depends": "Depends on Foundation",
    "dependencies": True,
}
PLAN_LAYERS_TEMPLATE = (
    "# Tasks: Layer Planner Case\n\n## Phase 1: Foundation\n\n{foundation}\n\n"
    "## Phase 2: User Story 1 - Emit Stable Plan (Priority: P1)\n\n{story}\n{extra_phase}{notes}"
)
PLAN_LAYERS_DEPENDENCIES = (
    "\n## Dependencies & Execution Order\n\n### Phase Dependencies\n\n"
    "- **Foundation**: No prerequisites.\n- **US1**: {us1_depends}.\n\n"
    "### Incremental Delivery\n\n1. Complete Foundation: T001\n2. Complete US1: T002\n"
)


def plan_layers_tasks(**overrides: object) -> str:
    """The baseline valid tasks.md with the named parts replaced."""
    parts = {**PLAN_LAYERS_BASELINE, **overrides}
    text = PLAN_LAYERS_TEMPLATE.format(**parts)
    return text + (PLAN_LAYERS_DEPENDENCIES.format(**parts) if parts["dependencies"] else "")


class PlanLayersPlannerCaseTests(unittest.TestCase):
    """Each case is one defect in an otherwise valid tasks.md, run through the real helper."""

    def plan(self, tasks_md: str) -> tuple[int, dict[str, object]]:
        with helper_project() as root:
            files = {**{name: "x\n" for name in PLAN_LAYERS_FILES}, "specs/feature/tasks.md": tasks_md}
            for relative, text in files.items():
                (root / relative).parent.mkdir(parents=True, exist_ok=True)
                (root / relative).write_text(text, encoding="utf-8")
            completed, response, _ = run_runner(
                helper_request("plan-layers-feature-dir", {"feature_dir": "specs/feature"}),
                cwd=root,
            )
        return completed.returncode, response["data"]["stdout_json"]

    def test_the_baseline_is_a_clean_plan(self) -> None:
        code, planner = self.plan(plan_layers_tasks())
        self.assertEqual((code, planner["status"], planner["errors"], planner["warnings"]), (0, "ok", [], []))

    def test_checkbox_state_and_parallel_marker_are_preserved(self) -> None:
        code, planner = self.plan(plan_layers_tasks(
            foundation="- [ ] T001 Unchecked in src/contract.md\n- [x] T003 Lowercase in src/planner.py\n"
                       "- [X] T004 Uppercase in tests/test_planner.py",
            story="- [ ] T002 [P] [US1] Parallel in src/planner.py",
        ))
        tasks = {task["id"]: task for inc in planner["increments"] for task in inc["tasks"]}
        self.assertEqual({k: v["status"] for k, v in tasks.items()},
                         {"T001": "todo", "T002": "todo", "T003": "done", "T004": "done"})
        self.assertEqual(code, 0)
        self.assertEqual({key for key, value in tasks.items() if value["parallel"]}, {"T002"})

    def test_a_defective_plan_reports_each_error_code(self) -> None:
        phase_3 = "\n## Phase 3: User Story 2 - Parse Ordered Increments (Priority: P1)\n\nNo tasks.\n"
        cases = {
            "empty increment": ({"extra_phase": phase_3}, ["empty_increment"]),
            "unknown dependency": ({"us1_depends": "Depends on US3"}, ["unknown_increment"]),
            "missing headings": (
                {"dependencies": False, "notes": "\n## Notes\n\nNo dependency or delivery headings.\n"},
                ["missing_required_heading", "missing_required_heading"],
            ),
        }
        for name, (overrides, codes) in cases.items():
            with self.subTest(case=name):
                code, planner = self.plan(plan_layers_tasks(**overrides))
                self.assertEqual((code, planner["status"]), (1, "invalid_plan"))
                self.assertEqual([error["code"] for error in planner["errors"]], codes)

    def test_reference_problems_are_warnings_not_errors(self) -> None:
        cases = {
            "missing files": (
                {"story": "- [ ] T002 [US1] Use src/no-such.py and tests/no-such-test.py"},
                [("reference_not_found", "src/no-such.py"), ("reference_not_found", "tests/no-such-test.py")],
            ),
            "no references": (
                {"foundation": "- [ ] T001 Prepare it", "story": "- [ ] T002 [US1] Build it"},
                [("task_without_references", "T001"), ("task_without_references", "T002")],
            ),
        }
        for name, (overrides, expected) in cases.items():
            with self.subTest(case=name):
                code, planner = self.plan(plan_layers_tasks(**overrides))
                self.assertEqual((code, planner["status"], planner["errors"]), (0, "ok", []))
                found = [(w["code"], w["details"].get("reference") or w["details"].get("task_id"))
                         for w in planner["warnings"]]
                self.assertEqual(found, expected)


class G0SetupTests(unittest.TestCase):
    @staticmethod
    def fixture_files(root: Path) -> dict[str, bytes]:
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}

    @staticmethod
    def prepare_fixture(root: Path, quality_text: str | None) -> None:
        subprocess.run(["git", "init", "-q", "-b", "test-g0", str(root)], check=True)
        for name in ("speckit-specify", "speckit-plan", "speckit-tasks", "speckit-implement"):
            skill = root / ".agents" / "skills" / name / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("fixture", encoding="utf-8")
        constitution = root / ".specify" / "memory" / "constitution.md"
        constitution.parent.mkdir()
        constitution.write_text("fixture", encoding="utf-8")
        (root / "workflow.md").write_text("fixture", encoding="utf-8")
        if quality_text is not None:
            (root / ".specify" / "quality-gates.json").write_text(quality_text, encoding="utf-8")

    def test_g0_setup_matches_golden_outcomes(self) -> None:
        from speckit_pro_runner.helpers.g0_setup import g0_setup

        manifest = json.loads((FIXTURE_DIR / "fixture-manifest.json").read_text(encoding="utf-8"))
        cases = next(row["golden_outcomes"] for row in manifest["helpers"] if row["helper_id"] == "g0-setup")
        for case in cases:
            for surface in ("claude", "codex"):
                with self.subTest(case=case["name"], surface=surface), helper_project() as root:
                    self.prepare_fixture(root, case["quality_text"])
                    before = self.fixture_files(root)
                    for probe in ("prerequisites", "commands", "presets"):
                        with patch("speckit_pro_runner.helpers.read_only.find_specify", return_value=case["specify"]), \
                                patch("speckit_pro_runner.helpers.read_only.verified_specify_executable",
                                      return_value=Path("/fixture/bin/specify") if case["specify"] else None), \
                                patch("speckit_pro_runner.helpers.read_only.installed_specify_version", return_value=None):
                            actual = g0_setup({"surface": surface, "probe": probe, "workflow_file": "workflow.md"}, root)
                        actual = json.loads(json.dumps(actual).replace(str(PLUGIN_ROOT), "<plugin-root>").replace(str(REPO_ROOT), "<repo-root>"))
                        self.assertEqual(case["probes"][probe], actual["result"])
                        if probe == "commands":
                            self.assertEqual(case["quality_gate"][surface], actual["quality_gate"])
                    after = self.fixture_files(root)
                    self.assertEqual(before, after, "G0 setup probes must not write")

    def test_g0_setup_runner_rejects_invalid_requests_and_routes_both_hosts(self) -> None:
        base = {"probe": "commands", "surface": "codex", "workflow_file": WORKFLOW_FILE}
        for inputs in ({}, {**base, "probe": "unknown"}, {**base, "surface": "unknown"},
                       {**base, "extra": True}, {**base, "workflow_file": "../outside.md"}):
            with self.subTest(inputs=inputs):
                completed, report, _ = run_runner(helper_request("g0-setup", inputs))
                self.assertEqual(2, completed.returncode)
                self.assertEqual("input_error", report["status"])
        for surface in ("claude", "codex"):
            completed, report, _ = run_runner(helper_request("g0-setup", {**base, "surface": surface}))
            self.assertEqual(0, completed.returncode)
            self.assertEqual("commands", report["data"]["probe"])
            view = host_skill_root(surface) / "speckit-autopilot"
            skill = (view / "SKILL.md").read_text(encoding="utf-8")
            prereqs = (view / "references" / "prerequisites.md").read_text(encoding="utf-8")
            self.assertIn(f"to `{surface}`", skill)
            self.assertEqual(3, prereqs.count('"helper_id":"g0-setup"'))
            self.assertIn("data.quality_gate", prereqs)
            self.assertNotIn("G0 blocked:", prereqs)


class G0UnratifiedDefaultsTests(unittest.TestCase):
    def test_g0_records_each_current_observation_once_on_resume(self) -> None:
        from speckit_pro_runner.helpers.decisions_list import decisions_list
        from speckit_pro_runner.helpers.g0_setup import g0_setup, unratified_defaults

        with helper_project() as root:
            G0SetupTests.prepare_fixture(root, None)
            unrelated = dict(unratified_defaults({"status": "missing"}, "claude")["decision"],
                             affected_unit="deployment-region")
            decisions_list(root, {"workflow_file": "workflow.md", "entries": [unrelated]}, "apply")
            for text, should_record in ((None, True), (None, False), ("{", True), ("{", False)):
                with self.subTest(text=text, should_record=should_record):
                    if text is not None:
                        (root / ".specify/quality-gates.json").write_text(text, encoding="utf-8")
                    with patch("speckit_pro_runner.helpers.read_only.find_specify", return_value="specify"):
                        observed = g0_setup({"surface": "claude", "probe": "commands",
                                             "workflow_file": "workflow.md"}, root)["quality_gate"]["unratified_defaults"]
                    self.assertEqual(should_record, observed["record_decision"])
                    if observed["record_decision"]:
                        decisions_list(root, {"workflow_file": "workflow.md", "entries": [observed["decision"]]}, "apply")
            entries = decisions_list(root, {"workflow_file": "workflow.md"}, "read_only")["entries"]
            self.assertEqual(3, len(entries))
            self.assertIn("invalid: cannot parse JSON", entries[-1]["evidence"])

    def test_g0_summary_uses_the_threshold_owner(self) -> None:
        from speckit_pro_runner.helpers.g0_setup import unratified_defaults

        defaults = {"complexity": 7, "crap": 25, "mutation_score_floor": 70}
        with patch("speckit_pro_runner.helpers.g0_setup.SHIPPED_DEFAULTS", defaults):
            observed = unratified_defaults({"status": "missing"}, "codex")
        for text in ("complexity 7", "CRAP 25", "mutation-score floor 70"):
            self.assertIn(text, observed["flag"])
            self.assertIn(text, observed["decision"]["option_chosen"])

    def test_g0_observation_is_persisted_in_both_host_run_states(self) -> None:
        from speckit_pro_runner.host_parity import emit_host

        source = REPO_ROOT / "speckit-pro/skills/speckit-autopilot/references/prerequisites.md"
        for host in ("claude", "codex"):
            rendered = emit_host(source.read_text(encoding="utf-8"), host)
            with self.subTest(host=host):
                self.assertIn("record_decision", rendered)
                self.assertIn("as `quality_gate_observation` in `autopilot-state.json`", rendered)
                self.assertIn("Clear that key and `UNRATIFIED_FLAG`", rendered)

    def test_g0_continues_on_unratified_defaults_and_never_writes_the_file(self) -> None:
        from speckit_pro_runner.helpers.decisions_list import checked_entry, decisions_list
        from speckit_pro_runner.helpers.g0_setup import g0_setup

        for name, text, detail in (("missing", None, "missing"), ("invalid", "{", "invalid: cannot parse JSON")):
            with self.subTest(case=name), helper_project() as root:
                G0SetupTests.prepare_fixture(root, text)
                inputs = {"surface": "claude", "probe": "commands", "workflow_file": "workflow.md"}
                with patch("speckit_pro_runner.helpers.read_only.find_specify", return_value="specify"):
                    gate = g0_setup(inputs, root)["quality_gate"]
                self.assertEqual(("proceed", ""), (gate["verdict"], gate["message"]))
                observed = gate["unratified_defaults"]
                self.assertNotIn("\n", observed["flag"])
                self.assertIn(detail, observed["flag"])
                self.assertIn(detail, observed["decision"]["evidence"])
                self.assertEqual(observed["decision"], checked_entry(observed["decision"]))
                self.assertEqual(text is not None, (root / ".specify" / "quality-gates.json").exists())
                if text is not None:
                    self.assertEqual(text, (root / ".specify" / "quality-gates.json").read_text(encoding="utf-8"))
                recorded = decisions_list(
                    root, {"workflow_file": "workflow.md", "entries": [observed["decision"]]}, "apply")
                self.assertEqual(["unratified_default"], [item["kind"] for item in recorded["entries"]])

    def test_unratified_flag_carries_no_markup_or_paths_from_file_content(self) -> None:
        from speckit_pro_runner import quality_gates
        from speckit_pro_runner.helpers.g0_setup import unratified_defaults

        hostile = "![x](https://evil.example/p.png) <img src=//evil/x> @org/admins \x1b[31m ‮ " + "/".join(("", "Users", "fixture", ".ssh")) + " `x`"
        problems = quality_gates.validate({hostile: 1})
        observed = unratified_defaults({"status": "invalid", "problems": problems}, "claude")
        text = observed["flag"] + observed["decision"]["evidence"]
        for fragment in ("![", "](", "<", "@", "\x1b", "‮", "/Users", "`x`"):
            self.assertNotIn(fragment, text)
        self.assertIn("unknown top-level keys", observed["flag"])

    def test_g0_present_file_raises_no_unratified_observation(self) -> None:
        from speckit_pro_runner.helpers.g0_setup import g0_setup

        valid = '{"schema_version": "1.0", "thresholds": {"complexity": 8, "crap": 30, "mutation_score_floor": 60}}'
        with helper_project() as root:
            G0SetupTests.prepare_fixture(root, valid)
            with patch("speckit_pro_runner.helpers.read_only.find_specify", return_value="specify"):
                gate = g0_setup({"surface": "codex", "probe": "commands", "workflow_file": "workflow.md"}, root)
        self.assertNotIn("unratified_defaults", gate["quality_gate"])


class G0BaselineStageTests(unittest.TestCase):
    """The project baseline (typecheck, tests, build, lint) belongs to implement entry, not plan-stage G0."""

    SCRIPTS = {"typecheck": "tsc", "test": "vitest", "test:integration": "vitest run it", "build": "tsc -b", "lint": "eslint ."}

    def commands_data(self, root: Path, surface: str, **extra: object) -> dict[str, object]:
        from speckit_pro_runner.helpers.g0_setup import g0_setup

        with patch("speckit_pro_runner.helpers.read_only.find_specify", return_value="/usr/bin/specify"), \
                patch("speckit_pro_runner.helpers.read_only.installed_specify_version", return_value=None):
            return g0_setup({"surface": surface, "probe": "commands", "workflow_file": "workflow.md", **extra}, root)

    def test_recorded_project_commands_supply_missing_slots_and_override_detection(self) -> None:
        for surface in ("claude", "codex"):
            with self.subTest(surface=surface), helper_project() as root:
                G0SetupTests.prepare_fixture(root, None)
                (root / "package.json").write_text(json.dumps({"scripts": {"test": "vitest", "lint": "eslint ."}}), encoding="utf-8")
                data = self.commands_data(root, surface, project_commands={
                    "TYPECHECK": "python3 tools/typecheck.py", "UNIT_TEST": "python3 tools/test.py",
                    "LINT": "N/A", "FULL_VERIFY": "python3 tools/verify.py",
                })
                self.assertEqual([], data["baseline"]["plan_stage"])
                self.assertEqual([
                    {"slot": "TYPECHECK", "command": "python3 tools/typecheck.py"},
                    {"slot": "UNIT_TEST", "command": "python3 tools/test.py"},
                ], data["baseline"]["implement_entry"])

    def test_plan_stage_g0_runs_no_project_command_and_implement_entry_records_the_baseline(self) -> None:
        for surface in ("claude", "codex"):
            with self.subTest(surface=surface), helper_project() as root:
                G0SetupTests.prepare_fixture(root, None)
                (root / "package.json").write_text(json.dumps({"scripts": self.SCRIPTS}), encoding="utf-8")
                before = G0SetupTests.fixture_files(root)
                with patch("subprocess.Popen", wraps=subprocess.Popen) as spawned:
                    data = self.commands_data(root, surface)
                self.assertEqual(before, G0SetupTests.fixture_files(root), "plan-stage G0 must not write")
                for call in spawned.call_args_list:
                    argv = call.args[0] if call.args else call.kwargs.get("args")
                    argv = argv.split() if isinstance(argv, str) else list(argv)
                    self.assertNotIn(argv[0], {"npm", "pnpm", "yarn", "bun"}, f"plan-stage G0 ran a project command: {argv}")
                baseline = data["baseline"]
                self.assertEqual([], baseline["plan_stage"])
                self.assertEqual(
                    [("BUILD", "npm build"), ("TYPECHECK", "npm typecheck"), ("LINT", "npm lint"),
                     ("UNIT_TEST", "npm test"), ("INTEGRATION_TEST", "npm test:integration")],
                    [(row["slot"], row["command"]) for row in baseline["implement_entry"]],
                )

    def test_a_project_without_a_command_slot_plans_only_the_slots_it_has(self) -> None:
        with helper_project() as root:
            G0SetupTests.prepare_fixture(root, None)
            (root / "package.json").write_text(json.dumps({"scripts": {"test": "vitest"}}), encoding="utf-8")
            baseline = self.commands_data(root, "codex")["baseline"]
            self.assertEqual([], baseline["plan_stage"])
            self.assertEqual(["UNIT_TEST"], [row["slot"] for row in baseline["implement_entry"]])

    def test_guidance_runs_the_baseline_at_implement_entry_on_both_hosts(self) -> None:
        for surface in ("claude", "codex"):
            with self.subTest(surface=surface):
                view = host_skill_root(surface) / "speckit-autopilot" / "references"
                phases = (view / "phase-execution.md").read_text(encoding="utf-8")
                if surface == "claude":  # Codex runs Phase 0 from SKILL.md and prerequisites.md alone
                    plan_stage = phases.split("Phase 0: Prerequisites", 1)[1].split("Phase 1: Specify", 1)[0]
                    for slot in ("TYPECHECK", "UNIT_TEST", "INTEGRATION_TEST", "BUILD", "LINT"):
                        self.assertNotIn(slot, plan_stage, f"plan-stage Phase 0 must not run {slot}")
                skill = (view.parent / "SKILL.md").read_text(encoding="utf-8")
                step = skill.split("4. **Constitution validation**", 1)[1].split("\n5. **", 1)[0]
                self.assertNotIn("PROJECT_COMMANDS", step)
                entry = phases.split("#### Phase 7 Setup: Project Baseline", 1)[1].split("#### Phase 7 Setup:", 1)[0]
                self.assertIn("`data.baseline.implement_entry`", entry)
                self.assertIn("blocked-for-UAT", entry)
                prereqs = (view / "prerequisites.md").read_text(encoding="utf-8")
                step_09 = prereqs.split("## Step 0.9: Constitution Validation", 1)[1].split("\n## Step 0.1", 1)[0]
                self.assertNotIn("PROJECT_COMMANDS", step_09)
                gates = (view / "gate-validation.md").read_text(encoding="utf-8")
                g0 = gates.split("### G0", 1)[1].split("### G1", 1)[0]
                self.assertNotIn("TYPECHECK command", g0)


class G0PinTests(unittest.TestCase):
    def test_g0_setup_preserves_advisory_version_statuses(self) -> None:
        from speckit_pro_runner.helpers.g0_setup import g0_setup

        cases = (("1.1.0", "match"), ("1.0.0", "older"), ("1.10.0", "newer"),
                 (None, "unreadable"), (None, "missing"))
        for surface in ("claude", "codex"):
            for version, status in cases:
                with self.subTest(surface=surface, status=status), helper_project() as root:
                    G0SetupTests.prepare_fixture(root, None)
                    found = status != "missing"
                    with patch("speckit_pro_runner.helpers.read_only.find_specify", return_value="specify" if found else None), \
                            patch("speckit_pro_runner.helpers.read_only.verified_specify_executable",
                                  return_value=Path("/fixture/bin/specify") if found else None), \
                            patch("speckit_pro_runner.helpers.read_only.installed_specify_version", return_value=version):
                        data = g0_setup({"surface": surface, "probe": "prerequisites", "workflow_file": "workflow.md"}, root)
                    result = data["result"]
                    report = result["stdout_json"]
                    self.assertEqual(status, report["spec_kit"]["status"])
                    self.assertEqual(version or ("unparsed" if found else None), report["spec_kit"]["installed_version"])
                    self.assertEqual(found, report["all_pass"])
                    self.assertEqual(0 if found else 1, result["exit_code"])
                    if found:
                        row = next(row for row in report["checks"] if row["check"] == "speckit_cli_version")
                        self.assertTrue(row["pass"], "G0 must preserve advisory version checks")


class G0SetupFailureTests(unittest.TestCase):
    def test_g0_setup_failed_probe_keeps_standalone_status_and_diagnostic(self) -> None:
        from types import SimpleNamespace
        from speckit_pro_runner.helpers.g0_setup import run_g0_setup_helper

        with helper_project() as root:
            G0SetupTests.prepare_fixture(root, None)
            inputs = {"probe": "prerequisites", "surface": "claude", "workflow_file": "workflow.md"}
            request = SimpleNamespace(request_id="g0", inputs=inputs)
            previous = Path.cwd()
            os.chdir(root)
            try:
                with patch("speckit_pro_runner.helpers.read_only.find_specify", return_value=None):
                    report = run_g0_setup_helper(None, request)
            finally:
                os.chdir(previous)
        self.assertEqual("expected_failure", report["status"], report)
        self.assertEqual(["validation_failure"], [row["code"] for row in report["diagnostics"]])
        self.assertEqual("check-prerequisites", report["diagnostics"][0]["details"]["helper_id"])


class ScaffoldAnswersTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)
        self.document = {
            "schema_version": "scaffold-answers/v1", "spec_id": "SPEC-009",
            "answers": {
                "goals": "List and inspect saved items.", "non_goals": "Network access.",
                "module_interface_deltas": "Two CLI subcommands.", "terms": "Item: a saved entry.",
                "verification_gates": "pytest", "design_tree": "Why CLI? Scriptable local use.",
                "open_questions": "None.", "bootstrap_commands": [],
                "quality_gate_confirmation": True, "formal_methods": False, "verification_docker": False,
                "continue_to_planning": False,
            },
        }

    def check(self, **inputs):
        (self.root / "answers.json").write_text(json.dumps(self.document), encoding="utf-8")
        _, result, _ = run_runner(helper_request("scaffold-answers", {
            "answers_file": "answers.json", "spec_id": "SPEC-009", **inputs,
        }), cwd=self.root)
        return result

    def test_missing_answer_names_the_key_and_stops(self):
        del self.document["answers"]["formal_methods"]
        result = self.check()
        self.assertEqual("expected_failure", result["status"], result)
        self.assertIn("formal_methods", result["data"]["problems"][0])
        self.assertEqual("stop", result["data"]["verdict"])

    def test_unknown_key_or_answer_names_the_key(self):
        for key, value in (("surprise", True), ("goals", "unknown"), ("formal_methods", "maybe"),
                           ("bootstrap_commands", ["python3 -m venv .venv"]),
                           ("bootstrap_commands", ["python3 -c 'from pathlib import Path; Path(\"bootstrap-ran\").touch()'"])):
            with self.subTest(key=key):
                previous = self.document["answers"].copy()
                self.document["answers"][key] = value
                result = self.check()
                self.assertEqual("expected_failure", result["status"])
                self.assertIn(key, str(result["data"]["problems"]))
                self.assertFalse(result["data"]["questions_allowed"])
                self.assertFalse((self.root / "bootstrap-ran").exists())
                self.document["answers"] = previous

    def test_complete_file_returns_answers_without_questions_or_writes(self):
        result = self.check()
        self.assertEqual("ok", result["status"])
        self.assertEqual(self.document["answers"], result["data"]["answers"])
        self.assertFalse(result["data"]["questions_allowed"])
        self.assertEqual(["answers.json"], sorted(path.name for path in self.root.iterdir()))


def receipt():
    return {
        "schema_version": "canary-receipt/v2", "commit": "a" * 40, "host": "codex",
        "host_version": "0.1.0", "plugin_version": "1.0.0", "fixture_tag": "fixture-v5",
        "trigger": "local", "dirty_tree": True, "release_status_allowed": False,
        "install_probe": {"headless_install": "passed", "skill_expansion": "passed", "evidence": "probe.json"},
        "variants": [{
            "name": "base", "verdict": "pass", "failed_assertions": [],
            "umask": "077", "task_list_calls": 0, "questions_after_scaffold": 0,
            "unregistered_stops": 0, "planning_end": "artifacts_and_draft_pr",
            "implement_end": "ready_for_uat", "uat_runbook": "uat.md",
            "decisions_by_kind": {"design": 2}, "retry_attempts": 0, "blocked_for_uat": 0,
            "feature_offers": {feature: {"evaluated": True, "offered": True, "answer": "declined"}
                               for feature in ("formal_methods", "verification_docker")},
            "plan_quality": {
                "phases_run": ["specify", "clarify", "plan", "checklist", "tasks", "analyze"], "clarify_sessions": 1,
                "requirements_total": 4, "untraced_requirements": [], "open_gaps": [], "open_findings": [],
                "open_clarifications": [], "blocked_for_uat_listed": [],
                "planted_catches": {"catch-1": "fixed", "catch-2": "fixed"},
                "decisions": {"total": 5, "low_confidence": 1, "consensus_rounds_by_kind": {"security": 1, "low_confidence": 1}},
            },
            "stages": {name: {"wall_seconds": 1, "tokens": 10, "codex_tokens": {"root_tokens": 10, "child_rollout_tokens": []}} for name in ("scaffold", "plan", "plan_review", "implement")},
        }],
    }


def hook_counters():
    phases = {"after_specify": 1, "after_plan": 1, "after_tasks": 1}
    return {"schema_version": "hook-counters/v1", "hooks": {
        kind: {"command": f"speckit.canary.{kind}", "optional": kind == "optional", "fires": 3,
               "phases": dict(phases), "unattributed_fires": 0} for kind in ("mandatory", "optional")}}


class CanaryReceiptTests(unittest.TestCase):
    def setUp(self):
        self.validator = load_script("canary_receipt", REPO_ROOT / "tests/speckit-pro/layer6-integration/validate-canary-receipt.py")

    def test_accepts_a_well_formed_local_receipt_for_each_host(self):
        for host in ("claude-code", "codex"):
            value = receipt()
            value["host"] = host
            if host == "claude-code":
                value["install_probe"] = {"loaded_plugins": ["speckit-pro@1.0.0"], "evidence": "init.json"}
                for stage in value["variants"][0]["stages"].values():
                    stage.pop("codex_tokens")
            self.assertEqual([], self.validator.validate_receipt(value))

    def test_rejects_questions_nonterminal_plan_missing_runbook_and_unregistered_stop(self):
        for key, bad in (("questions_after_scaffold", 1), ("planning_end", "paused"),
                         ("uat_runbook", ""), ("unregistered_stops", 1)):
            with self.subTest(key=key):
                value = copy.deepcopy(receipt())
                value["variants"][0][key] = bad
                self.assertTrue(self.validator.validate_receipt(value), key)

    def test_rejects_base_tools_failures_and_local_release_status(self):
        for key, bad in (("umask", "022"), ("task_list_calls", 1), ("verdict", "fail")):
            with self.subTest(key=key):
                value = receipt()
                value["variants"][0][key] = bad
                self.assertTrue(self.validator.validate_receipt(value), key)
        value = receipt()
        value["release_status_allowed"] = True
        self.assertTrue(self.validator.validate_receipt(value))

    def test_rejects_a_failed_codex_probe(self):
        value = receipt()
        value["install_probe"]["skill_expansion"] = "failed"
        self.assertTrue(self.validator.validate_receipt(value))

    def test_rejects_nonfinite_stage_evidence_through_api_and_cli(self):
        for number in (float("nan"), float("inf"), -float("inf")):
            value = receipt()
            value["variants"][0]["stages"]["plan"]["wall_seconds"] = number
            with self.subTest(number=str(number)), tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / "receipt.json"
                source.write_text(json.dumps(value), encoding="utf-8")
                completed = subprocess.run([sys.executable, self.validator.__file__, str(source)],
                                           capture_output=True, text=True, check=False)
                self.assertEqual(1, completed.returncode, completed.stdout)
                report = self.validator.receipt_report(value)
                self.assertFalse(report["valid"])
                json.dumps(report, allow_nan=False)


class CanaryVariantCase(unittest.TestCase):
    """Synthetic receipt evidence shared by the variant assertion and contract tests."""

    def setUp(self):
        self.validator = load_script("canary_receipt", REPO_ROOT / "tests/speckit-pro/layer6-integration/validate-canary-receipt.py")
        self.receipts = {host: receipt() for host in ("claude-code", "codex")}
        for host, value in self.receipts.items():
            value["host"] = host
            if host == "claude-code":
                value["install_probe"] = {"loaded_plugins": ["speckit-pro@1.0.0"], "evidence": "init.json"}
                for stage in value["variants"][0]["stages"].values():
                    stage.pop("codex_tokens")
        self.variant_evidence = {
            "base": {}, "missing_question_guard": {
                "verdict": "fail", "failed_assertions": ["question_guard"], "question_guard": {
                    "gap_recorded": True, "guarded_work_completed": 0, "guarded_work_passed": 0,
                },
            },
            "oversized_plan": {"split_recommendation_recorded": True, "full_plan_built": True, "stops": 0},
            "security_interrupt": {"questions_after_scaffold": 1, "security_interrupt": {
                "runner_permit_verified": True, "simulated_responder_answered": True, "pause_classification": "authorized",
            }},
            "security_block": {"blocked_for_uat": 2, "security_block": {
                "affected_work": 2, "affected_work_blocked_for_uat": 2,
                "independent_work": 3, "independent_work_completed": 3,
            }},
        }

    def catches(self, value):
        return value["variants"][0]["plan_quality"]["planted_catches"]

    def assert_variant_mutations(self, name, mutations):
        for host, value in self.receipts.items():
            variant = value["variants"][0]
            variant.update(name=name, **copy.deepcopy(self.variant_evidence[name]))
            with self.subTest(host=host):
                self.assertEqual([], self.validator.validate_receipt(value))
            for changes, assertion in mutations:
                mutated = copy.deepcopy(value)
                for path, bad in changes.items():
                    *parent, key = path.split(".")
                    target = mutated["variants"][0]
                    (target[parent[0]] if parent else target)[key] = bad
                with self.subTest(host=host, changes=changes):
                    self.assertEqual([f"{name}.{assertion}"], self.validator.validate_receipt(mutated))


class CanaryFeatureOfferTests(CanaryVariantCase):
    def test_base_requires_both_features_evaluated_offered_and_declined(self):
        for feature in ("formal_methods", "verification_docker"):
            for key, bad in (("evaluated", False), ("offered", False), ("answer", "accepted")):
                with self.subTest(feature=feature, key=key):
                    value = receipt()
                    value["variants"][0]["feature_offers"][feature][key] = bad
                    self.assertEqual(["base.feature_offers"], self.validator.validate_receipt(value))
        for broken in ({}, {"formal_methods": receipt()["variants"][0]["feature_offers"]["formal_methods"]}):
            with self.subTest(offers=sorted(broken)):
                value = receipt()
                value["variants"][0]["feature_offers"] = broken
                self.assertTrue(self.validator.validate_receipt(value))
        value = receipt()
        del value["variants"][0]["feature_offers"]
        self.assertTrue(self.validator.validate_receipt(value))


class CanaryVariantAssertionsTests(CanaryVariantCase):
    def test_oversized_plan_requires_split_full_build_and_no_stop(self):
        self.assert_variant_mutations("oversized_plan", [
            ({"split_recommendation_recorded": False}, "split_recommendation_recorded"),
            ({"full_plan_built": False}, "full_plan_built"), ({"stops": 1}, "stops"),
        ])

    def test_security_interrupt_requires_one_permitted_answered_authorized_pause(self):
        self.assert_variant_mutations("security_interrupt", [
            ({"security_interrupt.runner_permit_verified": False}, "runner_permit_verified"),
            ({"security_interrupt.simulated_responder_answered": False}, "simulated_responder_answered"),
            ({"security_interrupt.pause_classification": "unregistered"}, "pause_classification"),
            ({"security_interrupt.pause_classification": "not_observed"}, "pause_classification"),
            ({"questions_after_scaffold": 0}, "questions_after_scaffold"),
            ({"questions_after_scaffold": 2}, "questions_after_scaffold"),
        ])

    def test_missing_question_guard_is_red_even_at_handoff(self):
        for host, value in self.receipts.items():
            value["variants"][0]["name"] = "missing_question_guard"
            with self.subTest(host=host, claimed_verdict="pass"):
                self.assertEqual(["missing_question_guard.question_guard"], self.validator.validate_receipt(value))
            value["variants"][0].update(verdict="fail", failed_assertions=["question_guard"])
            with self.subTest(host=host, claimed_verdict="fail"):
                self.assertEqual(["missing_question_guard.verdict", "missing_question_guard.question_guard"],
                                 self.validator.validate_receipt(value))

    def test_security_block_requires_all_affected_blocked_and_all_independent_finished(self):
        def bad_counts(**counts):
            return {f"security_block.{key}": count for key, count in counts.items()}, "security_block"

        # Zeroing a count with its matching count isolates each "> 0" guard from the equality checks.
        self.assert_variant_mutations("security_block", [
            bad_counts(affected_work=0, affected_work_blocked_for_uat=0),
            bad_counts(affected_work_blocked_for_uat=1), bad_counts(affected_work_blocked_for_uat=3),
            bad_counts(independent_work=0, independent_work_completed=0),
            bad_counts(independent_work_completed=2), bad_counts(independent_work_completed=4),
            ({"blocked_for_uat": 1}, "security_block"),
        ])


class CanaryGateVerdictTests(CanaryVariantCase):
    def test_expected_red_missing_guard_passes_gate_for_both_hosts(self):
        for host, value in self.receipts.items():
            base = value["variants"][0]
            value["variants"] = [dict(copy.deepcopy(base), name=name, **copy.deepcopy(evidence))
                                 for name, evidence in self.variant_evidence.items()]
            with self.subTest(host=host), tempfile.TemporaryDirectory() as directory:
                self.assertEqual([], self.validator.validate_receipt(value))
                source = Path(directory) / "receipt.json"
                source.write_text(json.dumps(value), encoding="utf-8")
                completed = subprocess.run([sys.executable, self.validator.__file__, str(source)],
                                           capture_output=True, text=True, check=False)
                report = json.loads(completed.stdout)
                self.assertEqual((0, True, []), (completed.returncode, report["valid"], report["failed_assertions"]))
                results = {variant["name"]: variant for variant in report["variants"]}
                self.assertEqual(set(self.variant_evidence), set(results))
                self.assertTrue(all(result["gate_verdict"] == "pass" for result in results.values()))
                self.assertEqual("fail", results["missing_question_guard"]["verdict"])
                self.assertIn("missing_question_guard.question_guard", results["missing_question_guard"]["failed_assertions"])
            release_cases = ((trigger, index, duplicate) for trigger in ("scheduled", "on_demand")
                             for index in range(len(value["variants"])) for duplicate in (False, True))
            for trigger, index, duplicate in release_cases:
                release = copy.deepcopy(value)
                release.update(trigger=trigger, dirty_tree=False, release_status_allowed=True)
                with self.subTest(host=host, trigger=trigger, index=index, duplicate=duplicate):
                    self.assertEqual([], self.validator.validate_receipt(release, hook_counters=hook_counters()))
                    removed = release["variants"].pop(index)
                    if duplicate:
                        release["variants"].extend([removed, copy.deepcopy(removed)])
                    failure = "receipt.variant_entry_limit: 6" if duplicate else "release.variants"
                    self.assertIn(failure, self.validator.validate_receipt(release, hook_counters=hook_counters()))


class CanaryGuardGapContractTests(CanaryVariantCase):
    def test_expected_red_rejects_clean_claims_and_other_failures(self):
        for host, value in self.receipts.items():
            value["variants"][0].update(name="missing_question_guard", **copy.deepcopy(self.variant_evidence["missing_question_guard"]))
            self.assertEqual([], self.validator.validate_receipt(value))
            red = ["missing_question_guard.verdict", "missing_question_guard.question_guard"]
            # A clean-looking variant or missing gap evidence loses the exception: both own failures reach the gate.
            mutations = [(path, bad, red) for path, bad in (
                ("verdict", "pass"), ("failed_assertions", []),
                ("failed_assertions", ["question_guard", "other_failure"]), ("question_guard", None),
                ("question_guard.gap_recorded", False), ("question_guard.guarded_work_completed", 1),
                ("question_guard.guarded_work_passed", 1))]
            # Any other failed assertion still gates on its own.
            mutations.extend((key, bad, [f"missing_question_guard.{key}"]) for key, bad in (
                ("unregistered_stops", 1), ("questions_after_scaffold", 1), ("planning_end", "paused"),
                ("implement_end", "paused"), ("uat_runbook", "")))
            # Malformed evidence fails closed at the schema.
            malformed = [(f"question_guard.{key}", bad) for key in value["variants"][0]["question_guard"]
                         for bad in (None, "unknown")]
            malformed.extend((f"question_guard.{key}", bad) for key in ("guarded_work_completed", "guarded_work_passed")
                             for bad in (-1, True, 0.5))
            mutations.extend((path, bad, "receipt.schema: ") for path, bad in malformed)
            for path, bad, expected in mutations:
                mutated = copy.deepcopy(value)
                *parent, key = path.split(".")
                target = mutated["variants"][0]
                target = target[parent[0]] if parent else target
                if bad is None:
                    del target[key]
                else:
                    target[key] = bad
                with self.subTest(host=host, path=path, bad=bad):
                    failures = self.validator.validate_receipt(mutated)
                    if isinstance(expected, str):
                        self.assertEqual(1, len(failures), failures)
                        self.assertTrue(failures[0].startswith(expected), failures)
                    else:
                        self.assertEqual(expected, failures)
            budget = copy.deepcopy(self.validator.load_budget())
            budget[host]["missing_question_guard"]["plan"]["wall_seconds"] = 0.5
            report = self.validator.receipt_report(value, budget)
            self.assertFalse(report["valid"])
            self.assertEqual("fail", report["variants"][0]["gate_verdict"])
            self.assertIn("missing_question_guard.plan.wall_seconds_budget", report["failed_assertions"])


class CanaryVariantContractTests(CanaryVariantCase):
    def test_variant_evidence_fails_closed_when_missing_or_malformed(self):
        for host, original in self.receipts.items():
            for name in ("oversized_plan", "security_interrupt", "security_block"):
                value = copy.deepcopy(original)
                variant = value["variants"][0]
                variant.update(name=name, **copy.deepcopy(self.variant_evidence[name]))
                nested = name in self.variant_evidence[name]
                evidence = variant[name] if nested else variant
                fields = tuple(evidence) if nested else tuple(self.variant_evidence[name])
                for key in fields:
                    previous = evidence.pop(key)
                    with self.subTest(host=host, name=name, missing=key):
                        self.assertEqual(["receipt.schema: 1"], self.validator.validate_receipt(value))
                    evidence[key] = "unknown"
                    with self.subTest(host=host, name=name, malformed=key):
                        failures = self.validator.validate_receipt(value)
                        self.assertEqual(1, len(failures), failures)
                        self.assertTrue(failures[0].startswith("receipt.schema: "), failures)
                    evidence[key] = previous
                if nested:
                    del variant[name]
                    with self.subTest(host=host, name=name, missing="object"):
                        self.assertEqual(["receipt.schema: 1"], self.validator.validate_receipt(value))

    def test_all_five_variants_keep_missing_guard_red_through_api_and_cli(self):
        for host, value in self.receipts.items():
            base = value["variants"][0]
            value["variants"] = [dict(copy.deepcopy(base), name=name, **copy.deepcopy(evidence))
                                 for name, evidence in self.variant_evidence.items()]
            value["variants"][1].update(verdict="pass", failed_assertions=[])
            del value["variants"][1]["question_guard"]
            with self.subTest(host=host), tempfile.TemporaryDirectory() as directory:
                self.assertEqual(["missing_question_guard.question_guard"], self.validator.validate_receipt(value))
                source = Path(directory) / "receipt.json"
                source.write_text(json.dumps(value), encoding="utf-8")
                completed = subprocess.run([sys.executable, self.validator.__file__, str(source)],
                                           capture_output=True, text=True, check=False)
                report = json.loads(completed.stdout)
                self.assertEqual((1, False, ["missing_question_guard.question_guard"]),
                                 (completed.returncode, report["valid"], report["failed_assertions"]))


class CanaryPlanTargetTests(CanaryVariantCase):
    def test_over_target_reports_false_without_failing_the_gate_for_either_host(self):
        for host, original in self.receipts.items():
            for metric, actual in (("wall_seconds", 1801), ("tokens", 15000001)):
                value = copy.deepcopy(original)
                variant = value["variants"][0]
                with self.subTest(host=host, metric=metric):
                    variant["stages"]["plan"].update(wall_seconds=1, tokens=10)
                    variant["stages"]["plan"][metric] = actual
                    if host == "codex":
                        variant["stages"]["plan"]["codex_tokens"]["root_tokens"] = variant["stages"]["plan"]["tokens"]
                    report = self.validator.receipt_report(value)
                    self.assertTrue(report["valid"], report)
                    result = report["variants"][0]
                    self.assertEqual("pass", result["gate_verdict"])
                    self.assertFalse(result["plan_target"]["target_met"])
                    self.assertEqual(actual, result["plan_target"][metric])
                    self.assertEqual(1800, result["plan_target"]["wall_seconds_limit"])
                    self.assertEqual(15000000, result["plan_target"]["tokens_limit"])
                    self.assertNotIn("plan_target", variant)


    def test_target_boundaries_are_reported_independently_of_an_explicit_budget(self):
        for host, original in self.receipts.items():
            for seconds, tokens in ((1800, 15000000), (1800.4, 15000000), (1800, 15000001)):
                value = copy.deepcopy(original)
                plan = value["variants"][0]["stages"]["plan"]
                plan.update(wall_seconds=seconds, tokens=tokens)
                if host == "codex":
                    plan["codex_tokens"]["root_tokens"] = tokens
                limits = copy.deepcopy(self.validator.load_budget())
                limits[host]["base"]["plan"] = {"wall_seconds": 1700, "tokens": 14000000}
                with self.subTest(host=host, seconds=seconds, tokens=tokens):
                    report = self.validator.receipt_report(value, limits)
                    self.assertFalse(report["valid"])
                    self.assertEqual(["base.plan.wall_seconds_budget", "base.plan.tokens_budget"],
                                     report["failed_assertions"])
                    target = report["variants"][0]["plan_target"]
                    self.assertFalse(target["target_met"])
                    self.assertEqual((seconds, tokens), (target["wall_seconds"], target["tokens"]))

    def test_cli_reports_an_over_target_receipt_as_valid_for_both_hosts(self):
        for host, value in self.receipts.items():
            value["variants"][0]["stages"]["plan"]["wall_seconds"] = 1801
            with self.subTest(host=host), tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / "receipt.json"
                source.write_text(json.dumps(value), encoding="utf-8")
                completed = subprocess.run([sys.executable, self.validator.__file__, str(source)],
                                           capture_output=True, text=True, check=False)
                report = json.loads(completed.stdout)
                self.assertEqual(0, completed.returncode, report)
                self.assertEqual("pass", report["variants"][0]["gate_verdict"])
                self.assertFalse(report["variants"][0]["plan_target"]["target_met"])


class CanaryPlanTargetContractTests(CanaryVariantCase):
    def test_receipts_reject_target_claims_and_limits_for_both_hosts(self):
        for host, original in self.receipts.items():
            for name in ("base", "oversized_plan"):
                for target in ({}, {"target_met": True}, {"wall_seconds_limit": 1800, "tokens_limit": 15000000}):
                    value = copy.deepcopy(original)
                    value["variants"][0].update(name=name, plan_target=target, **self.variant_evidence[name])
                    with self.subTest(host=host, name=name, target=target):
                        self.assertTrue(self.validator.validate_receipt(value))

    def test_only_the_base_variant_reports_the_target(self):
        for host, value in self.receipts.items():
            variant = value["variants"][0]
            variant.update(name="oversized_plan", **self.variant_evidence["oversized_plan"])
            with self.subTest(host=host):
                report = self.validator.receipt_report(value)
                self.assertTrue(report["valid"], report)
                self.assertNotIn("plan_target", report["variants"][0])


    def test_inconsistent_plan_tokens_cannot_report_target_met_through_api_or_cli(self):
        value = self.receipts["codex"]
        plan = value["variants"][0]["stages"]["plan"]
        plan.update(wall_seconds=1, tokens=16000000,
                    codex_tokens={"root_tokens": 10, "child_rollout_tokens": [20]})
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "receipt.json"
            source.write_text(json.dumps(value), encoding="utf-8")
            completed = subprocess.run([sys.executable, self.validator.__file__, str(source)],
                                       capture_output=True, text=True, check=False)
        self.assertEqual(1, completed.returncode, completed.stdout)
        for seam, report in (("api", self.validator.receipt_report(value)),
                             ("cli", json.loads(completed.stdout))):
            with self.subTest(seam=seam):
                self.assertFalse(report["valid"])
                self.assertEqual(["base.plan.tokens_sum"], report["failed_assertions"])
                self.assertEqual({"wall_seconds_limit": 1800, "tokens_limit": 15000000,
                                  "wall_seconds": 1, "tokens": 30, "target_met": False},
                                 report["variants"][0]["plan_target"])


class CanaryCodexTokenTests(CanaryVariantCase):
    def test_child_rollouts_are_included_in_the_plan_total_and_target(self):
        value = self.receipts["codex"]
        plan = value["variants"][0]["stages"]["plan"]
        plan.update(tokens=16000000, codex_tokens={"root_tokens": 9000000, "child_rollout_tokens": [4000000, 3000000]})
        report = self.validator.receipt_report(value)
        self.assertTrue(report["valid"], report)
        target = report["variants"][0]["plan_target"]
        self.assertEqual(16000000, target["tokens"])
        self.assertFalse(target["target_met"])
        for children, measured in (([15000000], 15000010), ([20], 30)):
            plan.update(tokens=10, codex_tokens={"root_tokens": 10, "child_rollout_tokens": children})
            with self.subTest(measured=measured):
                report = self.validator.receipt_report(value)
                self.assertFalse(report["valid"])
                self.assertEqual(["base.plan.tokens_sum"], report["failed_assertions"])
                target = report["variants"][0]["plan_target"]
                self.assertEqual(measured, target["tokens"])
                # A summed breakdown cannot establish success while the claimed total contradicts it.
                self.assertFalse(target["target_met"])


    def test_each_codex_stage_checks_its_sum_and_allows_equal_child_counts(self):
        for name in ("scaffold", "plan", "plan_review", "implement"):
            value = copy.deepcopy(self.receipts["codex"])
            stage = value["variants"][0]["stages"][name]
            stage.update(tokens=27, codex_tokens={"root_tokens": 7, "child_rollout_tokens": [10, 10]})
            with self.subTest(stage=name):
                self.assertEqual([], self.validator.validate_receipt(value))
                stage["tokens"] = 7
                self.assertIn(f"base.{name}.tokens_sum", self.validator.validate_receipt(value))
                stage["tokens"] = 27

    def test_codex_breakdown_fails_closed_when_missing_or_malformed(self):
        for name in ("scaffold", "plan", "plan_review", "implement"):
            for bad in (None, {}, {"root_tokens": 10}, {"root_tokens": True, "child_rollout_tokens": []},
                        {"root_tokens": 10, "child_rollout_tokens": [-1]},
                        {"root_tokens": 10, "child_rollout_tokens": [1.5]}):
                value = copy.deepcopy(self.receipts["codex"])
                stage = value["variants"][0]["stages"][name]
                if bad is None:
                    del stage["codex_tokens"]
                else:
                    stage["codex_tokens"] = bad
                with self.subTest(stage=name, bad=bad):
                    self.assertTrue(self.validator.validate_receipt(value))

    def test_claude_rejects_codex_breakdowns_on_every_stage(self):
        for name in ("scaffold", "plan", "plan_review", "implement"):
            value = copy.deepcopy(self.receipts["claude-code"])
            value["variants"][0]["stages"][name]["codex_tokens"] = {"root_tokens": 10, "child_rollout_tokens": []}
            with self.subTest(stage=name):
                self.assertTrue(self.validator.validate_receipt(value))

    def test_a_codex_stage_schema_error_is_reported_once(self):
        value = self.receipts["codex"]
        value["variants"][0]["stages"]["plan"]["wall_seconds"] = "bad"
        report = self.validator.receipt_report(value)
        self.assertEqual(["receipt.schema: 1"], report["failed_assertions"])

    def test_claude_uses_its_stage_total_without_a_codex_breakdown(self):
        value = self.receipts["claude-code"]
        report = self.validator.receipt_report(value)
        self.assertTrue(report["valid"], report)
        self.assertEqual(10, report["variants"][0]["plan_target"]["tokens"])


class CanaryTargetValidityCase(CanaryVariantCase):
    """Runs one receipt through the API and a copied CLI; it holds no tests of its own."""

    def setUp(self):
        super().setUp()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.cli = self.root / "tests/speckit-pro/layer6-integration/validate-canary-receipt.py"
        self.cli.parent.mkdir(parents=True)
        shutil.copy2(self.validator.__file__, self.cli)
        shutil.copy2(Path(self.validator.__file__).with_name("canary-receipt.schema.json"), self.cli.parent)
        self.checked_cases = 0

    def complete_receipt(self, host):
        value = copy.deepcopy(self.receipts[host])
        base = value["variants"][0]
        value["variants"] = [dict(copy.deepcopy(base), name=name, **copy.deepcopy(evidence))
                             for name, evidence in ((name, self.variant_evidence[name]) for name in
                                                    ("base", "oversized_plan", "missing_question_guard", "security_interrupt", "security_block"))]
        return value

    def field_paths(self, value, path=()):
        children = value.items() if isinstance(value, dict) else enumerate(value) if isinstance(value, list) else ()
        for key, child in children:
            yield (*path, key)
            yield from self.field_paths(child, (*path, key))

    def changed(self, value, changes):
        value = copy.deepcopy(value)
        for path, bad in changes:
            parent = functools.reduce(lambda parent, key: parent[key], path[:-1], value)
            parent[path[-1]] = bad
        return value

    def assert_target_validity(self, value, counters, *, valid=False, failure=None, limits=None):
        limits = self.validator.load_budget() if limits is None else limits
        source, companion = self.root / "receipt.json", self.root / "hooks.json"
        source.write_text(json.dumps(value), encoding="utf-8")
        argv = [sys.executable, str(self.cli), str(source)]
        if counters is not self.validator.MISSING_HOOK_COUNTERS:
            companion.write_text(json.dumps(counters), encoding="utf-8")
            argv.extend(["--hook-counters", str(companion)])
        self.cli.with_name("canary-budget.json").write_text(json.dumps(
            {"schema_version": "canary-budget/v1", "policy": "test limits", "limits": limits}), encoding="utf-8")
        completed = subprocess.run(argv,
                                   env={**os.environ, "PYTHONPATH": str(PLUGIN_ROOT)},
                                   capture_output=True, text=True, check=False)
        self.assertEqual(int(not valid), completed.returncode, completed.stdout + completed.stderr)
        reports = (("api", self.validator.receipt_report(value, limits, hook_counters=counters)),
                   ("cli", json.loads(completed.stdout)))
        for seam, report in reports:
            with self.subTest(seam=seam):
                self.assertEqual(valid, report["valid"], report)
                if failure is not None:
                    self.assertIn(failure, report["failed_assertions"])
                if not valid:
                    self.assertTrue(report["failed_assertions"], report)
                targets = [result["plan_target"] for result in report["variants"] if "plan_target" in result]
                self.assertTrue(targets or not valid, report)
                for target in targets:
                    self.assertEqual(valid, target["target_met"], report)
        self.checked_cases += 1
        return dict(reports)


class CanaryReceiptTargetValidityTests(CanaryTargetValidityCase):
    """Every rejected receipt must reject target success, regardless of the failing field."""

    def test_each_receipt_and_hook_field_rejects_target_success_through_api_and_cli(self):
        for host in self.receipts:
            value, counters = self.complete_receipt(host), hook_counters()
            self.assert_target_validity(value, counters, valid=True)
            for document, original in (("receipt", value), ("hooks", counters)):
                for path in self.field_paths(original):
                    with self.subTest(host=host, document=document, path=path):
                        corrupted = self.changed(original, [(path, None)])
                        self.assert_target_validity(corrupted if document == "receipt" else value,
                                                    corrupted if document == "hooks" else counters)
        print(f"target validity field matrix: {self.checked_cases - 2} corruptions, API and CLI")

    def semantic_cases(self, value):
        base = ("variants", 0)
        for index, variant in enumerate(value["variants"]):
            name = variant["name"]
            for field, bad, label in (("verdict", "pass" if name == "missing_question_guard" else "fail", "verdict"),
                                      ("failed_assertions", ["other"], "verdict"),
                                      ("questions_after_scaffold", 0 if name == "security_interrupt" else 1, "questions_after_scaffold"),
                                      ("unregistered_stops", 1, "unregistered_stops"), ("planning_end", "paused", "planning_end"),
                                      ("implement_end", "paused", "implement_end"), ("uat_runbook", " ", "uat_runbook")):
                yield [(("variants", index, field), bad)], f"{name}.{label}"
            yield [(("variants", index, "plan_target"), {"target_met": True})], None
            if value["host"] == "codex":
                for stage in ("scaffold", "plan", "plan_review", "implement"):
                    yield [(("variants", index, "stages", stage, "tokens"), 11)], f"{name}.{stage}.tokens_sum"
        for field, bad in (("umask", "022"), ("task_list_calls", 1)):
            yield [(base + (field,), bad)], f"base.{field}"
        for feature in ("formal_methods", "verification_docker"):
            for field, bad in (("evaluated", False), ("offered", False), ("answer", "accepted")):
                yield [(base + ("feature_offers", feature, field), bad)], "base.feature_offers"
        quality = base + ("plan_quality",)
        for field, label in (("untraced_requirements", "untraced_requirements"), ("open_gaps", "open_gap"),
                             ("open_findings", "open_finding"), ("open_clarifications", "open_clarification"),
                             ("blocked_for_uat_listed", "blocked_for_uat_listed")):
            yield [(quality + (field,), ["item-1"])], f"base.plan_quality.{label}"
        phases = value["variants"][0]["plan_quality"]["phases_run"]
        for phase in phases:
            yield [(quality + ("phases_run",), [p for p in phases if p != phase])], "base.plan_quality.phases_run"
        for catch in ("catch-1", "catch-2"):
            yield [(quality + ("planted_catches", catch), "left_in_place")], f"base.plan_quality.planted_catches.{catch}"
        yield [(quality + ("planted_catches",), {})], "base.plan_quality.planted_catches.catch-1"
        if value["host"] == "codex":
            for field in ("headless_install", "skill_expansion"):
                yield [(("install_probe", field), "failed")], f"install_probe.{field}"
        else:
            yield [(("install_probe", "loaded_plugins"), [])], "install_probe.loaded_plugins"
            for stage in ("scaffold", "plan", "plan_review", "implement"):
                yield [(base + ("stages", stage, "codex_tokens"), {"root_tokens": 10, "child_rollout_tokens": []})], None
        yield [(("release_status_allowed",), True)], "local.release_status_allowed"
        for field, bad, label in (("split_recommendation_recorded", False, "split_recommendation_recorded"),
                                  ("full_plan_built", False, "full_plan_built"), ("stops", 1, "stops")):
            yield [(("variants", 1, field), bad)], f"oversized_plan.{label}"
        for field, bad in (("runner_permit_verified", False), ("simulated_responder_answered", False),
                           ("pause_classification", "unregistered")):
            yield [(("variants", 3, "security_interrupt", field), bad)], f"security_interrupt.{field}"
        yield [(("variants", 3, "questions_after_scaffold"), 0)], "security_interrupt.questions_after_scaffold"
        for field, bad in (("verdict", "pass"), ("failed_assertions", []), ("question_guard", {})):
            yield [(("variants", 2, field), bad)], None
        for field, bad in (("gap_recorded", False), ("guarded_work_completed", 1), ("guarded_work_passed", 1)):
            yield [(("variants", 2, "question_guard", field), bad)], "missing_question_guard.question_guard"
        for field in ("affected_work", "affected_work_blocked_for_uat", "independent_work", "independent_work_completed"):
            yield [(("variants", 4, "security_block", field), 0)], "security_block.security_block"
        yield [(("variants", 4, "blocked_for_uat"), 1)], "security_block.security_block"

    def test_each_semantic_failure_rejects_target_success_through_api_and_cli(self):
        for host in self.receipts:
            value = self.complete_receipt(host)
            for changes, failure in self.semantic_cases(value):
                with self.subTest(host=host, changes=changes):
                    self.assert_target_validity(self.changed(value, changes), hook_counters(), failure=failure)
        print(f"target validity semantic matrix: {self.checked_cases} corruptions, API and CLI")

    def test_release_hooks_input_and_budgets_reject_target_success_through_api_and_cli(self):
        for host in self.receipts:
            value, counters = self.complete_receipt(host), hook_counters()
            self.assert_target_validity(dict(value, unexpected=True), counters)
            release = dict(copy.deepcopy(value), trigger="scheduled", dirty_tree=False, release_status_allowed=True)
            self.assert_target_validity(release, counters, valid=True)
            for changes in ((("fixture_tag",), "other"), (("variants",), release["variants"][:-1])):
                self.assert_target_validity(self.changed(release, [changes]), counters)
            self.assert_target_validity(release, None)
            self.assert_target_validity(release, self.validator.MISSING_HOOK_COUNTERS, failure="hook_counters.missing")
            for kind in ("mandatory", "optional"):
                for field, bad in (("optional", kind == "mandatory"), ("fires", 0), ("unattributed_fires", 1)):
                    self.assert_target_validity(value, self.changed(counters, [(("hooks", kind, field), bad)]))
                for event in ("after_specify", "after_plan", "after_tasks"):
                    self.assert_target_validity(value, self.changed(counters, [(("hooks", kind, "phases", event), 0)]))
            for stage in ("scaffold", "plan", "implement"):
                for metric, limit in (("wall_seconds", 0.5), ("tokens", 1)):
                    limits = self.validator.load_budget()
                    limits[host]["base"][stage][metric] = limit
                    self.assert_target_validity(value, counters, limits=limits, failure=f"base.{stage}.{metric}_budget")
            for bad in (float("nan"), float("inf"), float("-inf")):
                self.assert_target_validity(self.changed(value, [(("variants", 0, "stages", "plan", "wall_seconds"), bad)]), counters)
            for catches in ({"unknown": "fixed"}, {f"catch-{n}": "fixed" for n in range(3)}):
                self.assert_target_validity(self.changed(value, [(("variants", 0, "plan_quality", "planted_catches"), catches)]), counters)
            self.assert_target_validity(dict(value, variants=value["variants"] + [value["variants"][0]]), counters)
        print(f"target validity release/hooks/input/budget matrix: {self.checked_cases - 2} corruptions, API and CLI")

    def test_cli_read_and_parse_failures_never_report_target_success(self):
        value = self.complete_receipt("codex")
        self.assert_target_validity(value, hook_counters(), valid=True)
        source = self.root / "receipt.json"
        bodies = (b"not json", b'{"host":"codex","host":"codex"}', b"\xff", b"[" * 3000,
                  b" " * (self.validator.MAX_RECEIPT_BYTES + 1), None)
        for body in bodies:
            with self.subTest(input_kind=None if body is None else body[:30]):
                if body is None:
                    source.unlink()
                else:
                    source.write_bytes(body)
                completed = subprocess.run([sys.executable, str(self.cli), str(source)],
                                           env={**os.environ, "PYTHONPATH": str(PLUGIN_ROOT)},
                                           capture_output=True, text=True, check=False)
                report = json.loads(completed.stdout)
                self.assertEqual(1, completed.returncode, report)
                self.assertFalse(report["valid"], report)
                self.assertEqual([], report["variants"], report)
        print(f"target validity CLI input matrix: {len(bodies)} read/parse failures")


class CanaryVariantIdentityTests(CanaryTargetValidityCase):
    """Class: variant-identity ambiguity. A receipt whose variant names repeat has no single
    report per identity, so it must be invalid and publish no per-variant report or target."""

    TRIGGERS = ("local", "scheduled", "on_demand")

    def with_trigger(self, value, trigger):
        value = copy.deepcopy(value)
        if trigger != "local":
            value.update(trigger=trigger, dirty_tree=False, release_status_allowed=True)
        return value

    def set_plan(self, variant, metric, amount):
        plan = variant["stages"]["plan"]
        plan[metric] = amount
        if metric == "tokens" and "codex_tokens" in plan:
            plan["codex_tokens"] = {"root_tokens": amount, "child_rollout_tokens": []}

    def assert_ambiguous(self, value, name):
        reports = self.assert_target_validity(value, hook_counters(), failure=f"receipt.duplicate_variant: {name}")
        for seam, report in reports.items():
            with self.subTest(seam=seam):
                self.assertEqual([], report["variants"], report)

    def test_conflicting_base_duplicates_report_no_target_through_api_and_cli(self):
        for host in self.receipts:
            base = self.complete_receipt(host)["variants"][0]
            for trigger in self.TRIGGERS:
                for metric, over in (("wall_seconds", 1801), ("tokens", 15000001)):
                    for copies in range(2, len(self.validator.VARIANTS) + 1):
                        for position in range(copies):
                            entries = [copy.deepcopy(base) for _ in range(copies)]
                            self.set_plan(entries[position], metric, over)
                            value = dict(self.receipts[host], variants=entries)
                            with self.subTest(host=host, trigger=trigger, metric=metric, copies=copies, position=position):
                                self.assert_ambiguous(self.with_trigger(value, trigger), "base")
        print(f"variant identity base-conflict matrix: {self.checked_cases} receipts, API and CLI")

    def test_each_name_duplicated_at_each_position_is_ambiguous_through_api_and_cli(self):
        for host in self.receipts:
            complete = self.complete_receipt(host)
            for trigger in self.TRIGGERS:
                # Renaming one entry to an identity already present, for every source and position pair.
                for source, position in itertools.permutations(range(len(complete["variants"])), 2):
                    value = copy.deepcopy(complete)
                    value["variants"][position] = copy.deepcopy(value["variants"][source])
                    name = value["variants"][source]["name"]
                    with self.subTest(host=host, trigger=trigger, source=source, position=position):
                        self.assert_ambiguous(self.with_trigger(value, trigger), name)
                # Two through five entries of one identity, with no other entry.
                for variant in complete["variants"]:
                    for copies in range(2, len(self.validator.VARIANTS) + 1):
                        value = dict(complete, variants=[copy.deepcopy(variant) for _ in range(copies)])
                        with self.subTest(host=host, trigger=trigger, name=variant["name"], copies=copies):
                            self.assert_ambiguous(self.with_trigger(value, trigger), variant["name"])
        print(f"variant identity name/position matrix: {self.checked_cases} receipts, API and CLI")

    def test_a_repeated_mapping_reference_is_ambiguous_through_api_and_cli(self):
        for host in self.receipts:
            base = self.complete_receipt(host)["variants"][0]
            for copies in range(2, len(self.validator.VARIANTS) + 1):
                with self.subTest(host=host, copies=copies):
                    self.assert_ambiguous(dict(self.receipts[host], variants=[base] * copies), "base")

    def test_unique_identities_keep_one_report_per_variant(self):
        for host in self.receipts:
            for trigger in self.TRIGGERS:
                value = self.with_trigger(self.complete_receipt(host), trigger)
                with self.subTest(host=host, trigger=trigger):
                    reports = self.assert_target_validity(value, hook_counters(), valid=True)
                    for report in reports.values():
                        names = [result["name"] for result in report["variants"]]
                        self.assertEqual(sorted(self.validator.VARIANTS), sorted(names))
                        self.assertEqual(1, sum("plan_target" in result for result in report["variants"]))

    def test_api_reports_from_one_snapshot_of_a_list_that_changes_between_reads(self):
        """A list that yields different entries to each read must not pass the identity check with one
        roster and report another."""
        for host in self.receipts:
            base = self.complete_receipt(host)["variants"][0]
            over = copy.deepcopy(base)
            self.set_plan(over, "wall_seconds", 1801)

            class ShiftingVariants(list):
                reads = 0

                def __iter__(self):
                    ShiftingVariants.reads += 1
                    return iter([base] if ShiftingVariants.reads < 4 else [over, base])

            value = dict(self.receipts[host], variants=ShiftingVariants([base]))
            report = self.validator.receipt_report(value)
            with self.subTest(host=host):
                targets = [result["plan_target"] for result in report["variants"] if "plan_target" in result]
                self.assertEqual(1, len(targets), report)
                self.assertEqual(report["valid"], targets[0]["target_met"], report)

    def test_duplicate_json_keys_on_every_target_selection_key_fail_closed_in_the_cli(self):
        """The CLI is the only seam that can see a repeated key; each one the target reads must fail closed."""
        repeats = (("host", "claude-code"), ("trigger", "scheduled"), ("variants", []), ("name", "oversized_plan"),
                   ("stages", {}), ("plan", {"wall_seconds": 1801, "tokens": 10}), ("wall_seconds", 1801),
                   ("tokens", 15000001), ("codex_tokens", {"root_tokens": 15000001, "child_rollout_tokens": []}),
                   ("root_tokens", 15000001), ("child_rollout_tokens", [15000001]))
        source = self.root / "receipt.json"
        for host in self.receipts:
            text = json.dumps(self.complete_receipt(host))
            for key, other in repeats:
                marker = f'"{key}": '
                if marker not in text:
                    continue  # claude-code stages carry no codex token keys
                with self.subTest(host=host, key=key):
                    source.write_text(text.replace(marker, f"{marker}{json.dumps(other)}, {marker}", 1), encoding="utf-8")
                    completed = subprocess.run([sys.executable, str(self.cli), str(source)],
                                               env={**os.environ, "PYTHONPATH": str(PLUGIN_ROOT)},
                                               capture_output=True, text=True, check=False)
                    report = json.loads(completed.stdout)
                    self.assertEqual((1, False, ["input.invalid"], []),
                                     (completed.returncode, report["valid"], report["failed_assertions"], report["variants"]))


class CanaryBudgetCase(unittest.TestCase):
    """Shared setup for the budget tests; it holds no tests of its own."""

    def setUp(self):
        self.validator = load_script("canary_receipt", REPO_ROOT / "tests/speckit-pro/layer6-integration/validate-canary-receipt.py")

    def budget(self, wall_seconds, tokens):
        """A complete budget whose limits are all ``wall_seconds`` and ``tokens``."""
        stages = {stage: {"wall_seconds": wall_seconds, "tokens": tokens} for stage in self.validator.BUDGET_STAGES}
        return {host: {variant: copy.deepcopy(stages) for variant in self.validator.VARIANTS} for host in self.validator.HOSTS}


class CanaryBudgetTests(CanaryBudgetCase):
    def test_a_stage_over_a_set_limit_fails_and_under_it_passes(self):
        value = receipt()
        self.assertEqual([], self.validator.validate_receipt(value, self.budget(5, 100)))
        for key, actual in (("wall_seconds", 6), ("tokens", 101)):
            value = receipt()
            value["variants"][0]["stages"]["plan"][key] = actual
            value["variants"][0]["stages"]["plan"]["codex_tokens"]["root_tokens"] = value["variants"][0]["stages"]["plan"]["tokens"]
            self.assertEqual([f"base.plan.{key}_budget"], self.validator.validate_receipt(value, self.budget(5, 100)), key)
        value["variants"][0]["stages"]["plan"].update(wall_seconds=5, tokens=100, codex_tokens={"root_tokens": 100, "child_rollout_tokens": []})
        self.assertEqual([], self.validator.validate_receipt(value, self.budget(5, 100)), "a stage at its limit is within budget")

    def test_an_overrun_belongs_only_to_the_variant_entry_that_ran_over(self):
        value = receipt()
        value["variants"].append(dict(copy.deepcopy(value["variants"][0]), name="oversized_plan",
                                      split_recommendation_recorded=True, full_plan_built=True, stops=0))
        value["variants"][1]["stages"]["plan"]["wall_seconds"] = 6
        report = self.validator.receipt_report(value, self.budget(5, 100))
        self.assertEqual(["oversized_plan.plan.wall_seconds_budget"], report["failed_assertions"])
        self.assertEqual(["pass", "fail"], [variant["gate_verdict"] for variant in report["variants"]])

    def test_an_unset_limit_reports_unbudgeted_and_never_a_pass(self):
        value = receipt()
        value["variants"][0]["stages"]["plan"]["tokens"] = 10**9
        value["variants"][0]["stages"]["plan"]["codex_tokens"]["root_tokens"] = 10**9
        unset = self.budget(5, None)
        report = self.validator.receipt_report(value, unset)
        self.assertEqual((True, []), (report["valid"], report["failed_assertions"]))
        self.assertEqual([f"base.{stage}.tokens" for stage in self.validator.BUDGET_STAGES], report["unbudgeted"])
        self.assertEqual([], self.validator.receipt_report(value, self.budget(5, 100))["unbudgeted"])
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "receipt.json"
            source.write_text(json.dumps(receipt()), encoding="utf-8")
            completed = subprocess.run([sys.executable, self.validator.__file__, str(source)],
                                       capture_output=True, text=True, check=False)
        output = json.loads(completed.stdout)
        self.assertEqual((0, True), (completed.returncode, output["valid"]), completed.stdout)
        self.assertEqual(len(self.validator.BUDGET_STAGES) * len(self.validator.METRICS), len(output["unbudgeted"]))

    def test_plan_review_is_recorded_but_never_budgeted(self):
        value = receipt()
        value["variants"][0]["stages"]["plan_review"].update(wall_seconds=10**6, tokens=10**9, codex_tokens={"root_tokens": 10**9, "child_rollout_tokens": []})
        self.assertEqual([], self.validator.validate_receipt(value, self.budget(5, 100)))



class CanaryBudgetFileTests(CanaryBudgetCase):
    def test_the_budget_file_covers_every_host_variant_and_stage_and_states_its_rule(self):
        document = json.loads(self.validator.BUDGET_FILE.read_text(encoding="utf-8"))
        limits = self.validator.load_budget()
        self.assertEqual(set(self.validator.HOSTS), set(limits))
        for host in self.validator.HOSTS:
            self.assertEqual(set(self.validator.VARIANTS), set(limits[host]), host)
            for stages in limits[host].values():
                self.assertEqual(set(self.validator.BUDGET_STAGES), set(stages), host)
        for phrase in ("median of the first three green runs plus 50%", "reviewed PR", "unbudgeted", "never stops a run"):
            self.assertIn(phrase, document["policy"])

    def test_a_malformed_budget_fails_closed(self):
        def document(limits):
            return {"schema_version": "canary-budget/v1", "policy": "rule", "limits": limits}

        complete = self.budget(5, 100)
        self.assertEqual(complete, self.validator.check_budget(document(complete)))
        huge = self.budget(10**400, 10**400)
        self.assertIs(huge, self.validator.check_budget(document(huge)), "a huge integer limit never overflows")
        broken = []
        for stage_limits in ({"wall_seconds": 0, "tokens": 1}, {"wall_seconds": 1, "tokens": 1.5},
                             {"wall_seconds": True, "tokens": 1}, {"wall_seconds": 1, "tokens": 1, "extra": 1}, {"tokens": 1}):
            limits = copy.deepcopy(complete)
            limits["codex"]["base"]["plan"] = stage_limits
            broken.append(document(limits))
        extra = copy.deepcopy(complete)
        extra["codex"]["base"]["plan_review"] = {"wall_seconds": 1, "tokens": 1}
        broken += [document(extra), document({**complete, "codex": []}), {**document(complete), "schema_version": "v0"}, [], None]
        for value in broken:
            with self.assertRaises(ValueError, msg=value):
                self.validator.check_budget(value)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "budget.json"
            for text in ("[]", json.dumps(document(extra)), json.dumps(document(complete)).replace("100", "NaN", 1)):
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError, msg=text):
                    self.validator.load_budget(path)

    def test_nothing_in_the_plugin_stops_a_run_on_budget(self):
        stop_policy = load_script("stop_policy_for_budget", REPO_ROOT / "speckit-pro/speckit_pro_runner/stop_policy.py")
        self.assertFalse([reason for reason in stop_policy.STOP_REASONS if "budget" in reason])
        shipped = [path for path in (REPO_ROOT / "speckit-pro").rglob("*") if path.is_file()
                   and self.validator.BUDGET_FILE.name in path.read_text(encoding="utf-8", errors="ignore")]
        self.assertEqual([], shipped)


class CanaryPlanQualityTests(CanaryVariantCase):
    """ADR 0023 artifact checks and ADR 0021's six planning phases, for both hosts."""

    def quality(self, value):
        return value["variants"][0]["plan_quality"]

    def test_each_open_planning_item_fails_the_receipt(self):
        for host, value in self.receipts.items():
            for field, label in (("untraced_requirements", "untraced_requirements"), ("open_gaps", "open_gap"),
                                 ("open_findings", "open_finding"), ("open_clarifications", "open_clarification")):
                mutated = copy.deepcopy(value)
                self.quality(mutated)[field] = ["item-1"]
                with self.subTest(host=host, field=field):
                    self.assertEqual([f"base.plan_quality.{label}"], self.validator.validate_receipt(mutated))

    def test_a_blocked_and_listed_item_passes_but_an_unlisted_one_fails(self):
        for host, value in self.receipts.items():
            for field, item_id in (("open_gaps", "checklists/requirements.md:L12"),
                                   ("open_findings", "F001"), ("open_clarifications", "spec.md:L24")):
                mutated = copy.deepcopy(value)
                quality = self.quality(mutated)
                quality[field] = [item_id]
                quality["blocked_for_uat_listed"] = [item_id]
                mutated["variants"][0]["blocked_for_uat"] = 1
                with self.subTest(host=host, field=field, listed=True):
                    self.assertEqual([], self.validator.validate_receipt(mutated))
                mutated["variants"][0]["blocked_for_uat"] = 0
                with self.subTest(host=host, field=field, listed="not counted"):
                    self.assertEqual(["base.plan_quality.blocked_for_uat_listed"], self.validator.validate_receipt(mutated))
                mutated["variants"][0]["blocked_for_uat"] = 1
                quality["blocked_for_uat_listed"] = ["T001"]
                with self.subTest(host=host, field=field, listed=False):
                    self.assertEqual(1, len(self.validator.validate_receipt(mutated)))

    def test_every_planning_phase_must_have_run(self):
        for host, value in self.receipts.items():
            for phase in self.quality(value)["phases_run"]:
                mutated = copy.deepcopy(value)
                self.quality(mutated)["phases_run"].remove(phase)
                with self.subTest(host=host, missing=phase):
                    self.assertEqual(["base.plan_quality.phases_run"], self.validator.validate_receipt(mutated))

    def test_a_variant_that_never_reached_specify_fails(self):
        for host, value in self.receipts.items():
            mutated = copy.deepcopy(value)
            quality = self.quality(mutated)
            quality["phases_run"] = []
            with self.subTest(host=host, requirements=quality["requirements_total"]):
                self.assertEqual(["base.plan_quality.phases_run"], self.validator.validate_receipt(mutated))
            quality["requirements_total"] = 0
            with self.subTest(host=host, requirements=0):
                failures = self.validator.validate_receipt(mutated)
                self.assertEqual(["receipt.schema: 1"], failures)

    def test_the_clarify_session_count_and_decisions_are_required_evidence(self):
        for host, value in self.receipts.items():
            for field, bad in (("clarify_sessions", None), ("clarify_sessions", -1), ("decisions", None),
                               ("requirements_total", 0)):
                mutated = copy.deepcopy(value)
                if bad is None:
                    del self.quality(mutated)[field]
                else:
                    self.quality(mutated)[field] = bad
                with self.subTest(host=host, field=field, bad=bad):
                    failures = self.validator.validate_receipt(mutated)
                    self.assertEqual(["receipt.schema: 1"], failures)

    def test_plan_quality_is_required_on_every_variant(self):
        for host, value in self.receipts.items():
            mutated = copy.deepcopy(value)
            del mutated["variants"][0]["plan_quality"]
            with self.subTest(host=host):
                self.assertTrue(self.validator.validate_receipt(mutated))


class CanaryHookCounterTests(CanaryVariantCase):
    """ADR 0023: each registered hook fires exactly once per phase."""

    def test_one_fire_per_hook_per_phase_passes_for_both_hosts(self):
        for host, value in self.receipts.items():
            with self.subTest(host=host):
                self.assertEqual([], self.validator.validate_receipt(value, hook_counters=hook_counters()))

    def test_a_hook_fired_twice_or_never_fails_the_receipt(self):
        for host, value in self.receipts.items():
            for kind in ("mandatory", "optional"):
                for event, fires in (("after_specify", 2), ("after_plan", 0), ("after_tasks", 2)):
                    counters = hook_counters()
                    counters["hooks"][kind]["phases"][event] = fires
                    counters["hooks"][kind]["fires"] = sum(counters["hooks"][kind]["phases"].values())
                    with self.subTest(host=host, kind=kind, event=event, fires=fires):
                        self.assertEqual([f"hook_counters.{kind}.{event}"],
                                         self.validator.validate_receipt(value, hook_counters=counters))

    def test_unattributed_fires_fail_the_receipt(self):
        counters = hook_counters()
        counters["hooks"]["optional"]["unattributed_fires"] = 1
        counters["hooks"]["optional"]["fires"] = 4
        self.assertEqual(["hook_counters.optional.unattributed_fires"],
                         self.validator.validate_receipt(self.receipts["codex"], hook_counters=counters))

    def test_inconsistent_totals_or_a_swapped_optional_flag_fail_the_receipt(self):
        for field, bad in (("fires", 0), ("optional", True)):
            counters = hook_counters()
            counters["hooks"]["mandatory"][field] = bad
            self.assertEqual([f"hook_counters.mandatory.{field}"],
                             self.validator.validate_receipt(self.receipts["codex"], hook_counters=counters))

    def test_malformed_counters_fail_closed(self):
        for host, value in self.receipts.items():
            with self.subTest(host=host, counters=None):
                self.assertTrue(self.validator.validate_receipt(value, hook_counters=None))
        for mutate in (lambda c: c["hooks"].pop("optional"), lambda c: c.update(schema_version="other"),
                       lambda c: c["hooks"]["mandatory"]["phases"].pop("after_tasks")):
            counters = hook_counters()
            mutate(counters)
            failures = self.validator.validate_receipt(self.receipts["codex"], hook_counters=counters)
            self.assertTrue(failures and failures[0].startswith("hook_counters"), failures)

    def test_a_release_receipt_without_counters_fails_but_a_local_one_does_not(self):
        value = self.receipts["codex"]
        self.assertEqual([], self.validator.validate_receipt(value))
        value.update(trigger="scheduled", dirty_tree=False, release_status_allowed=True)
        self.assertIn("hook_counters.missing", self.validator.validate_receipt(value))
        self.assertNotIn("hook_counters.missing", self.validator.validate_receipt(value, hook_counters=hook_counters()))

    def test_cli_reads_the_companion_receipt(self):
        value = self.receipts["claude-code"]
        for fires, expected in ((1, 0), (2, 1), (None, 1)):
            counters = None if fires is None else hook_counters()
            if counters is not None:
                counters["hooks"]["mandatory"]["phases"]["after_plan"] = fires
            with self.subTest(fires=fires), tempfile.TemporaryDirectory() as directory:
                source, companion = Path(directory) / "receipt.json", Path(directory) / "hook-counters-receipt.json"
                source.write_text(json.dumps(value), encoding="utf-8")
                companion.write_text(json.dumps(counters), encoding="utf-8")
                completed = subprocess.run([sys.executable, self.validator.__file__, str(source),
                                            "--hook-counters", str(companion)],
                                           capture_output=True, text=True, check=False)
                self.assertEqual(expected, completed.returncode, completed.stdout)


class CanaryPlantedCatchTests(CanaryVariantCase):
    """ADR 0023: the base receipt asserts the plan fixed each planted catch, read against the pinned fixture tag."""

    def test_the_pinned_fixture_has_two_catch_ids(self):
        self.assertEqual(("catch-1", "catch-2"), self.validator.PLANTED_CATCH_IDS)

    def test_a_catch_left_in_place_fails_the_receipt(self):
        for host, value in self.receipts.items():
            for catch in self.validator.PLANTED_CATCH_IDS:
                mutated = copy.deepcopy(value)
                self.catches(mutated)[catch] = "left_in_place"
                with self.subTest(host=host, catch=catch):
                    self.assertEqual([f"base.plan_quality.planted_catches.{catch}"],
                                     self.validator.validate_receipt(mutated))

    def test_a_missing_or_unknown_catch_record_fails_closed(self):
        for host, value in self.receipts.items():
            missing = copy.deepcopy(value)
            del self.catches(missing)["catch-2"]
            unknown = copy.deepcopy(value)
            self.catches(unknown)["catch-3"] = "fixed"
            absent = copy.deepcopy(value)
            del absent["variants"][0]["plan_quality"]["planted_catches"]
            with self.subTest(host=host, case="missing"):
                self.assertEqual(["base.plan_quality.planted_catches.catch-2"], self.validator.validate_receipt(missing))
            with self.subTest(host=host, case="unknown"):
                self.assertEqual(["planted_catches.entry_limit: 3"], self.validator.validate_receipt(unknown))
            with self.subTest(host=host, case="absent"):
                self.assertEqual(["base.plan_quality.planted_catches"], self.validator.validate_receipt(absent))

    def test_an_unrecognised_status_fails_schema_validation(self):
        for host, value in self.receipts.items():
            self.catches(value)["catch-1"] = "maybe"
            with self.subTest(host=host):
                report = self.validator.receipt_report(value)
                self.assertFalse(report["valid"])
                self.assertEqual(["receipt.schema: 1"], report["failed_assertions"])
                self.assertEqual([], report["variants"])

    def test_a_release_receipt_must_name_the_pinned_fixture_tag(self):
        self.assertEqual("fixture-v5", self.validator.FIXTURE_TAG)
        for host, value in self.receipts.items():
            value.update(trigger="scheduled", dirty_tree=False, release_status_allowed=True)
            with self.subTest(host=host, tag="pinned"):
                self.assertNotIn("release.fixture_tag", self.validator.validate_receipt(value, hook_counters=hook_counters()))
            value["fixture_tag"] = "fixture-v4"
            with self.subTest(host=host, tag="older"):
                self.assertIn("release.fixture_tag", self.validator.validate_receipt(value, hook_counters=hook_counters()))
            value.update(trigger="local", dirty_tree=True, release_status_allowed=False)
            with self.subTest(host=host, tag="local"):
                self.assertEqual([], self.validator.validate_receipt(value))

    def test_the_budget_note_names_the_tag_and_the_lock_ticket(self):
        policy = json.loads(self.validator.BUDGET_FILE.read_text(encoding="utf-8"))["policy"]
        self.assertIn(self.validator.FIXTURE_TAG, policy)
        self.assertIn("#1199", policy)


class CanaryCatchInputTests(CanaryVariantCase):
    """Untrusted catch ids produce only bounded, constant diagnostics."""

    def test_many_unknown_catches_have_one_bounded_failure(self):
        for host, value in self.receipts.items():
            prefix = "unknown-" + "x" * 64
            self.catches(value).update({f"{prefix}{index}": "fixed" for index in range(10000)})
            with self.subTest(host=host), tempfile.TemporaryDirectory() as directory:
                report = self.validator.receipt_report(value)
                self.assertEqual(1, len(report["failed_assertions"]))
                self.assertEqual(["planted_catches.entry_limit: 10002"], report["failed_assertions"])
                self.assertLess(len(json.dumps(report)), 256)
                source = Path(directory) / "receipt.json"
                source.write_text(json.dumps(value), encoding="utf-8")
                completed = subprocess.run([sys.executable, self.validator.__file__, str(source)],
                                           capture_output=True, text=True, check=False)
                self.assertLess(source.stat().st_size, 1024 * 1024)
                self.assertEqual(1, completed.returncode)
                self.assertEqual(report, json.loads(completed.stdout))
                self.assertLess(len(completed.stdout), 256)
                self.assertEqual("", completed.stderr)

    def test_unknown_catch_names_never_appear_in_api_or_cli_output(self):
        marker = chr(27) + "[31m" + chr(10) + "/" + "synthetic-marker/receipt.txt"
        for host, original in self.receipts.items():
            for status in ("fixed", "left_in_place", marker):
                value = copy.deepcopy(original)
                del self.catches(value)["catch-2"]
                self.catches(value)[marker] = status
                with self.subTest(host=host, status=status), tempfile.TemporaryDirectory() as directory:
                    report = self.validator.receipt_report(value)
                    self.assertEqual(["unknown planted-catch id: 1"], report["failed_assertions"])
                    self.assertLess(len(json.dumps(report)), 256)
                    source = Path(directory) / "receipt.json"
                    source.write_text(json.dumps(value), encoding="utf-8")
                    completed = subprocess.run([sys.executable, self.validator.__file__, str(source)],
                                               capture_output=True, text=True, check=False)
                    self.assertEqual(1, completed.returncode)
                    self.assertEqual(report, json.loads(completed.stdout))
                    self.assertNotIn("synthetic-marker", completed.stdout + completed.stderr)
                    self.assertLess(len(completed.stdout), 256)

    def test_multiple_unknown_ids_are_one_counted_failure_on_any_variant(self):
        for host, value in self.receipts.items():
            for name in self.variant_evidence:
                value["variants"][0]["name"] = name
                catches = self.catches(value)
                catches.clear()
                catches.update({"unknown-one": "fixed", "unknown-two": "fixed"})
                with self.subTest(host=host, variant=name):
                    self.assertEqual(["unknown planted-catch id: 2"], self.validator.validate_receipt(value))

    def test_the_schema_rejects_unknown_catch_ids(self):
        value = self.receipts["codex"]
        self.assertEqual([], self.validator.json_schema_failures(value, self.validator.SCHEMA, self.validator.SCHEMA, "receipt"))
        self.catches(value)["catch-3"] = "fixed"
        self.assertTrue(self.validator.json_schema_failures(value, self.validator.SCHEMA, self.validator.SCHEMA, "receipt"))


class CanaryReceiptOutputTests(CanaryVariantCase):
    """Receipt and companion schema diagnostics carry only constant identifiers and counts."""

    def test_nonfinite_and_overflow_reports_are_strict_json_for_both_hosts(self):
        for host, original in self.receipts.items():
            for literal in ("NaN", "Infinity", "-Infinity", "1e400", "-1e400"):
                value = copy.deepcopy(original)
                value["variants"][0]["stages"]["plan"]["wall_seconds"] = 12345.5
                body = json.dumps(value).replace("12345.5", literal)
                with self.subTest(host=host, literal=literal), tempfile.TemporaryDirectory() as directory:
                    report = self.validator.receipt_report(json.loads(body))
                    self.assertFalse(report["valid"], report)
                    json.dumps(report, allow_nan=False)
                    source = Path(directory) / "receipt.json"
                    source.write_text(body, encoding="utf-8")
                    completed = subprocess.run([sys.executable, self.validator.__file__, str(source)],
                                               capture_output=True, text=True, check=False)
                    self.assertEqual(1, completed.returncode, completed.stdout)
                    output = json.loads(completed.stdout, parse_constant=self.validator.reject_nonfinite)
                    self.assertFalse(output["valid"])
                    self.assertEqual("", completed.stderr)

    def test_schema_errors_never_reflect_supplied_keys_or_values(self):
        marker = "untrusted-schema-marker"
        for host, original in self.receipts.items():
            for mutate in (lambda v: v.update({marker: marker}),
                           lambda v: v["variants"][0].update(name=marker),
                           lambda v: self.catches(v).update({"catch-1": marker})):
                value = copy.deepcopy(original)
                mutate(value)
                with self.subTest(host=host):
                    report = self.validator.receipt_report(value)
                    self.assertEqual(1, len(report["failed_assertions"]))
                    self.assertRegex(report["failed_assertions"][0], r"^receipt\.schema: [0-9]+$")
                    self.assertNotIn(marker, json.dumps(report))

    def test_hook_schema_errors_never_reflect_supplied_keys(self):
        counters = hook_counters()
        counters["hooks"]["untrusted-hook-marker"] = "untrusted-hook-marker"
        report = self.validator.receipt_report(self.receipts["codex"], hook_counters=counters)
        self.assertEqual(["hook_counters.schema: 1"], report["failed_assertions"])
        self.assertNotIn("untrusted-hook-marker", json.dumps(report))

    def test_extra_variants_cannot_multiply_catch_output(self):
        value = self.receipts["codex"]
        value["variants"] *= 10000
        report = self.validator.receipt_report(value)
        self.assertEqual(["receipt.variant_entry_limit: 10000"], report["failed_assertions"])
        self.assertLess(len(json.dumps(report)), 256)


class CanaryReceiptInputTests(CanaryVariantCase):
    """Receipt reads and parsing fail closed within the byte cap."""

    def test_cli_receipt_byte_limit_is_inclusive_and_precedes_json_parsing(self):
        limit = 1024 * 1024
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "receipt.json"
            body = json.dumps(self.receipts["codex"]).encode("utf-8")
            multibyte = copy.deepcopy(self.receipts["codex"])
            multibyte["host_version"] = "é" * (limit // 2)
            cases = ((body + b" " * (limit - len(body)), True, []),
                     (body + b" " * (limit + 1 - len(body)), False, ["input.byte_limit: 1048576"]),
                     (json.dumps(multibyte, ensure_ascii=False).encode("utf-8"), False, ["input.byte_limit: 1048576"]),
                     (b"!" * (limit + 1), False, ["input.byte_limit: 1048576"]))
            for payload, valid, failures in cases:
                source.write_bytes(payload)
                with self.subTest(size=len(payload), valid=valid):
                    completed = subprocess.run([sys.executable, self.validator.__file__, str(source)],
                                               capture_output=True, text=True, check=False)
                    self.assertEqual("", completed.stderr)
                    report = json.loads(completed.stdout)
                    self.assertEqual(int(not valid), completed.returncode)
                    self.assertEqual(valid, report["valid"])
                    self.assertEqual(failures, report["failed_assertions"])
                    self.assertEqual("", completed.stderr)
                    if not valid:
                        self.assertLess(len(completed.stdout), 256)

    def test_the_companion_receipt_has_the_same_byte_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "receipt.json"
            counters = Path(directory) / "counters.json"
            source.write_text(json.dumps(self.receipts["codex"]), encoding="utf-8")
            counters.write_bytes(b"!" * (1024 * 1024 + 1))
            completed = subprocess.run([sys.executable, self.validator.__file__, str(source), "--hook-counters", str(counters)],
                                       capture_output=True, text=True, check=False)
            self.assertEqual(1, completed.returncode)
            self.assertEqual(["input.byte_limit: 1048576"], json.loads(completed.stdout)["failed_assertions"])
            self.assertLess(len(completed.stdout), 256)
            self.assertEqual("", completed.stderr)

    def test_cli_parse_and_read_errors_are_constant(self):
        marker = "untrusted-input-marker"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / (marker + ".json")
            for payload in (None, b"\xff", (marker + " not JSON").encode(),
                            b"[" * 2000 + b"]" * 2000,
                            json.dumps({marker: marker}).replace("}", ', "' + marker + '": 0}').encode()):
                if payload is not None:
                    source.write_bytes(payload)
                with self.subTest(payload=payload is not None):
                    completed = subprocess.run([sys.executable, self.validator.__file__, str(source)],
                                               capture_output=True, text=True, check=False)
                    self.assertEqual(1, completed.returncode)
                    self.assertEqual("", completed.stderr)
                    report = json.loads(completed.stdout)
                    self.assertEqual(["input.invalid"], report["failed_assertions"])
                    self.assertNotIn(marker, completed.stdout + completed.stderr)
                    self.assertLess(len(completed.stdout), 256)
                    self.assertEqual("", completed.stderr)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--helper", choices=EXPECTED_HELPERS)
    args = parser.parse_args()
    _ReadOnlyHelperRunner.helper_filter = args.helper
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                               for case in (SpecKitExecutableReuseTests, ReadOnlyHelperTests, PlanLayersRepairRouteTests, PlanLayersPlannerCaseTests,
                                            PacketTitlePatternTests, G0SetupTests, G0BaselineStageTests, G0PinTests, G0UnratifiedDefaultsTests, G0SetupFailureTests, ScaffoldAnswersTests, CanaryReceiptTests,
                                            CanaryFeatureOfferTests, CanaryVariantAssertionsTests, CanaryVariantContractTests,
                                            CanaryGateVerdictTests, CanaryGuardGapContractTests,
                                            CanaryPlanTargetTests, CanaryPlanTargetContractTests, CanaryCodexTokenTests,
                                            CanaryReceiptTargetValidityTests, CanaryVariantIdentityTests,
                                            CanaryPlanQualityTests, CanaryPlantedCatchTests, CanaryCatchInputTests, CanaryReceiptInputTests,
                                            CanaryReceiptOutputTests, CanaryHookCounterTests, CanaryBudgetTests, CanaryBudgetFileTests))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed
    print(f"test-speckit-pro-read-only-helpers: {passed}/{total} passed")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
