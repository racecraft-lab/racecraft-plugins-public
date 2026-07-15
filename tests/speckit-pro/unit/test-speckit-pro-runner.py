#!/usr/bin/env python3
"""Stdlib-only tests for the XPLAT-004 SpecKit Pro runner."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
RUNNER_DIR = PLUGIN_ROOT / "speckit_pro_runner"
sys.path.insert(0, str(PLUGIN_ROOT))
FIXTURE_FILE = Path(__file__).resolve().parent / "fixtures" / "speckit-pro-runner" / "contract-fixtures.json"
RUNBOOK_FILE = Path(__file__).resolve().parent / "fixtures" / "speckit-pro-runner" / "platform-runbook-fixtures.md"
CHANGED_FILES_FILE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "speckit-pro-runner"
    / "runner-foundation-changed-files.txt"
)


def runner_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(PLUGIN_ROOT) if not existing else f"{PLUGIN_ROOT}{os.pathsep}{existing}"
    return env


def encode_request(request: object) -> str:
    if isinstance(request, str):
        return request
    return json.dumps(request)


def run_runner(request: object) -> tuple[subprocess.CompletedProcess[str], dict[str, object] | None, list[dict[str, object]]]:
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=encode_request(request),
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        env=runner_env(),
        shell=False,
        check=False,
    )
    response = json.loads(completed.stdout) if completed.stdout.strip() else None
    stderr_records = [json.loads(line) for line in completed.stderr.splitlines() if line.strip()]
    return completed, response, stderr_records


def changed_paths_against_review_base() -> list[str]:
    candidates = ["origin/main...HEAD"]
    parents = subprocess.run(
        ["git", "rev-list", "--parents", "-n", "1", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if parents.returncode == 0 and len(parents.stdout.split()) >= 3:
        candidates.append("HEAD^1...HEAD")

    errors = []
    for candidate in candidates:
        completed = subprocess.run(
            ["git", "diff", "--name-only", candidate],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode == 0:
            return [line for line in completed.stdout.splitlines() if line]
        errors.append(f"{candidate}: {completed.stderr.strip() or completed.stdout.strip()}")

    if CHANGED_FILES_FILE.is_file():
        changed = [line for line in CHANGED_FILES_FILE.read_text(encoding="utf-8").splitlines() if line]
        if changed:
            return changed

    raise AssertionError(f"Unable to diff changed paths against review base: {'; '.join(errors)}")


def changed_status_against_review_base() -> dict[str, str]:
    candidates = ["origin/main...HEAD"]
    parents = subprocess.run(
        ["git", "rev-list", "--parents", "-n", "1", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if parents.returncode == 0 and len(parents.stdout.split()) >= 3:
        candidates.append("HEAD^1...HEAD")

    errors = []
    for candidate in candidates:
        completed = subprocess.run(
            ["git", "diff", "--name-status", candidate],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode == 0:
            status_by_path: dict[str, str] = {}
            for line in completed.stdout.splitlines():
                parts = line.split("\t")
                if len(parts) < 2:
                    continue
                status_by_path[parts[-1]] = parts[0][0]
            return status_by_path
        errors.append(f"{candidate}: {completed.stderr.strip() or completed.stdout.strip()}")

    if CHANGED_FILES_FILE.is_file():
        return {
            line: "M"
            for line in CHANGED_FILES_FILE.read_text(encoding="utf-8").splitlines()
            if line
        }

    raise AssertionError(f"Unable to diff changed path statuses against review base: {'; '.join(errors)}")


def base_request(operation: str = "runtime-info", inputs: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "request_id": f"test-{operation}",
        "helper_id": "runner",
        "operation": operation,
        "mode": "read_only",
        "inputs": inputs or {},
    }


def fixture_request(value: object) -> object:
    copied = copy.deepcopy(value)

    def replace(node: object) -> object:
        if isinstance(node, list):
            return [replace(item) for item in node]
        if isinstance(node, dict):
            return {key: replace(item) for key, item in node.items()}
        if node == "__PYTHON__":
            return sys.executable
        return node

    return replace(copied)


class RunnerFoundationTests(unittest.TestCase):
    def assert_diagnostic_shape(self, diagnostic: dict[str, object], code: str | None = None) -> None:
        for field in ("severity", "source", "code", "message", "remediation"):
            self.assertIn(field, diagnostic)
        self.assertEqual(diagnostic["source"], "runner")
        remediation = diagnostic["remediation"]
        self.assertIsInstance(remediation, dict)
        self.assertIn("summary", remediation)
        self.assertIn("actions", remediation)
        self.assertTrue(remediation["actions"])
        if code is not None:
            self.assertEqual(diagnostic["code"], code)

    def assert_response(self, response: dict[str, object], status: str, exit_code: int) -> None:
        self.assertEqual(response["schema_version"], "1.0")
        self.assertEqual(response["status"], status)
        self.assertEqual(response["exit_code"], exit_code)
        self.assertIsNone(response["legacy_exit_code"])
        self.assertIsInstance(response["diagnostics"], list)
        self.assertIsInstance(response["data"], dict)

    def test_runner_subprocess_executables_are_statically_bash_free(self) -> None:
        from speckit_pro_runner.gates.active_path_guard import repo_bash_python_findings

        paths = [
            PLUGIN_ROOT / "speckit_pro_runner" / "gates" / "suite.py",
            PLUGIN_ROOT / "speckit_pro_runner" / "helpers" / "install.py",
            PLUGIN_ROOT / "speckit_pro_runner" / "runtime.py",
        ]
        findings = [
            (path.relative_to(REPO_ROOT).as_posix(), finding.line, finding.pattern)
            for path in paths
            for finding in repo_bash_python_findings(
                path.relative_to(REPO_ROOT).as_posix(),
                path.read_text(encoding="utf-8"),
            )
        ]

        self.assertEqual(findings, [])

    def test_runtime_info_reports_source_checkout_identity(self) -> None:
        completed, response, stderr_records = run_runner(base_request("runtime-info"))
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(len(completed.stdout.strip().splitlines()), 1)
        self.assertEqual(stderr_records, [])
        self.assertIsNotNone(response)
        self.assert_response(response, "ok", 0)
        report = response["data"]["report"]
        self.assertEqual(report["runner_name"], "speckit_pro_runner")
        self.assertEqual(report["runner_contract_id"], "speckit-pro-runner")
        self.assertEqual(report["selected_runtime_name"], "python-stdlib-runner")
        self.assertEqual(report["source_vs_installed_context"], "source_checkout")
        self.assertIn("python_version", report)
        self.assertIn("platform", report)
        self.assertIn("architecture", report)
        self.assertEqual(report["metadata"]["verification_status"], "not_checked")
        for key in ("plugin_root", "runner_package", "manifest_file", "checksum_file"):
            path_record = report["paths"][key]
            self.assertEqual(path_record["kind"], "plugin_relative")
            self.assertFalse(Path(path_record["value"]).is_absolute())

    def test_preflight_ok_with_test_controlled_prerequisites(self) -> None:
        completed, response, stderr_records = run_runner(
            base_request(
                "preflight",
                {
                    "test_overrides": {
                        "specify": {"available": True, "path": "specify", "version": "0.11.8"},
                        "metadata_status": "verified",
                    }
                },
            )
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(stderr_records, [])
        self.assert_response(response, "ok", 0)
        report = response["data"]["report"]
        self.assertEqual(report["prerequisites"]["python"]["status"], "available")
        self.assertEqual(report["prerequisites"]["specify"]["status"], "available")
        self.assertEqual(report["metadata"]["verification_status"], "verified")

    def test_preflight_fail_closed_missing_prerequisites(self) -> None:
        cases = [
            ({"python_version": "3.10.9", "specify": {"available": True}, "metadata_status": "verified"}, "python_too_old"),
            ({"specify": {"available": False}, "metadata_status": "verified"}, "specify_missing"),
            ({"plugin_root": "missing", "specify": {"available": True}, "metadata_status": "verified"}, "plugin_root_missing"),
        ]
        for overrides, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                completed, response, stderr_records = run_runner(base_request("preflight", {"test_overrides": overrides}))
                self.assertEqual(completed.returncode, 3)
                self.assert_response(response, "missing_prerequisite", 3)
                codes = [diag["code"] for diag in response["diagnostics"]]
                self.assertIn(expected_code, codes)
                self.assertEqual([diag["code"] for diag in stderr_records], codes)
                for diag in response["diagnostics"]:
                    self.assert_diagnostic_shape(diag)

    def test_validation_failures(self) -> None:
        cases = [
            ("{", "invalid_json"),
            ({"schema_version": "9.0", "helper_id": "runner", "operation": "runtime-info", "mode": "read_only", "inputs": {}}, "unsupported_schema_version"),
            ({"schema_version": "1.0", "helper_id": "runner", "operation": "runtime-info", "mode": "read_only"}, "missing_required_field"),
            ({"schema_version": "1.0", "helper_id": "runner", "operation": "unsupported", "mode": "read_only", "inputs": {}}, "invalid_envelope"),
            ({"schema_version": "1.0", "helper_id": "mutation-foundation", "operation": "mutation-foundation", "mode": [], "inputs": {}}, "invalid_envelope"),
            ({"schema_version": "1.0", "helper_id": "runner", "operation": [], "mode": "read_only", "inputs": {}}, "invalid_envelope"),
        ]
        for request, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                completed, response, stderr_records = run_runner(request)
                self.assertEqual(completed.returncode, 2)
                self.assert_response(response, "input_error", 2)
                self.assertEqual([diag["code"] for diag in response["diagnostics"]], [expected_code])
                self.assertEqual([diag["code"] for diag in stderr_records], [expected_code])
                self.assert_diagnostic_shape(response["diagnostics"][0], expected_code)

    def test_contract_fixtures(self) -> None:
        fixtures = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))["fixtures"]
        self.assertGreaterEqual(len(fixtures), 10)
        forbidden = (
            "generate-spec-index.sh",
            "speckit-scaffold",
            "speckit-status",
            "speckit-autopilot",
            "install",
            "pr-packet",
        )
        for fixture in fixtures:
            with self.subTest(case_id=fixture["case_id"]):
                request = fixture["raw_request"] if "raw_request" in fixture else fixture_request(fixture["request"])
                request_blob = encode_request(request)
                if fixture["category"] not in {"envelope", "runtime-info"}:
                    for forbidden_text in forbidden:
                        self.assertNotIn(forbidden_text, request_blob)
                completed, response, stderr_records = run_runner(request)
                self.assertEqual(completed.returncode, fixture["expected_exit_code"])
                self.assert_response(response, fixture["expected_status"], fixture["expected_exit_code"])
                codes = [diag["code"] for diag in response["diagnostics"]]
                self.assertEqual(codes, fixture["expected_diagnostic_codes"])
                self.assertEqual([diag["code"] for diag in stderr_records], codes)
                for diag in response["diagnostics"]:
                    self.assert_diagnostic_shape(diag)
                if fixture.get("expected_remediation"):
                    self.assertTrue(response["diagnostics"][0]["remediation"]["actions"])
                if fixture["category"] == "typed_path" and fixture["expected_status"] == "ok":
                    result = response["data"]["fixture_result"]
                    self.assertTrue(result["accepted"])
                    self.assertEqual(result["path"]["value"], fixture["request"]["inputs"]["path"]["value"])
                if fixture["category"] == "subprocess":
                    result = response["data"]["subprocess"]
                    self.assertFalse(result["shell"])
                    self.assertIsInstance(result["argv"], list)
                    self.assertLessEqual(result["timeout_seconds"], 5)
                    self.assertIn("duration_ms", result)
                    for stream in ("stdout", "stderr"):
                        capture = result[stream]
                        self.assertEqual(capture["limit_bytes"], 16384)
                        self.assertIn("byte_count", capture)
                        self.assertIn("truncated", capture)

    def test_manifest_and_checksum_cover_runner_sources(self) -> None:
        manifest = json.loads((RUNNER_DIR / "speckit-pro-runner.manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["runner_name"], "speckit_pro_runner")
        self.assertEqual(manifest["runner_contract_id"], "speckit-pro-runner")
        self.assertEqual(manifest["selected_runtime_name"], "python-stdlib-runner")
        self.assertEqual(manifest["contract_version"], "1.0")
        # Version-agnostic: the runner manifest's plugin_version must be a valid
        # semantic version AND equal the released plugin version. release-please
        # bumps it via release-please-config.json extra-files ($.plugin_version),
        # so a hardcoded literal here would silently drift (the XPLAT-010 fix).
        plugin_version = json.loads(
            (PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )["version"]
        self.assertRegex(
            manifest["plugin_version"],
            r"^\d+\.\d+\.\d+$",
            "runner manifest plugin_version must be a semantic version",
        )
        self.assertEqual(
            manifest["plugin_version"],
            plugin_version,
            "runner manifest plugin_version must track speckit-pro/.claude-plugin/plugin.json $.version",
        )
        self.assertEqual(manifest["python_minimum_version"], "3.11")
        self.assertTrue(manifest["specify_required"])
        self.assertEqual(manifest["checksum_algorithm"], "sha256")

        expected = {}
        runner_sources = sorted(path for path in RUNNER_DIR.rglob("*.py") if "__pycache__" not in path.parts)
        for path in runner_sources:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            expected[path.relative_to(PLUGIN_ROOT).as_posix()] = digest

        checkout_attributes = subprocess.run(
            [
                "git",
                "check-attr",
                "eol",
                "--",
                *(path.relative_to(REPO_ROOT).as_posix() for path in runner_sources),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(checkout_attributes.returncode, 0, checkout_attributes.stderr)
        self.assertTrue(checkout_attributes.stdout.strip())
        for line in checkout_attributes.stdout.splitlines():
            path, attribute, value = line.rsplit(": ", 2)
            self.assertEqual(attribute, "eol")
            self.assertEqual(value, "lf", f"runner trust metadata requires LF checkout: {path}")

        manifest_records = {
            record["path"]["value"]: record["sha256"]
            for record in manifest["runner_files"]
        }
        self.assertEqual(manifest_records, expected)
        self.assertNotIn("speckit_pro_runner/speckit-pro-runner.manifest.json", manifest_records)
        self.assertNotIn("speckit_pro_runner/speckit-pro-runner.sha256", manifest_records)

        checksum_records = {}
        for line in (RUNNER_DIR / "speckit-pro-runner.sha256").read_text(encoding="utf-8").splitlines():
            digest, rel_path = line.split(maxsplit=1)
            checksum_records[rel_path] = digest
        self.assertEqual(checksum_records, expected)

    def test_metadata_readiness_failures(self) -> None:
        expected = {
            "missing_metadata": "runner_metadata_missing",
            "incomplete_metadata": "runner_metadata_incomplete",
            "mismatch": "runner_metadata_mismatch",
            "not_checked": "runner_metadata_not_checked",
        }
        for status, code in expected.items():
            with self.subTest(status=status):
                completed, response, stderr_records = run_runner(
                    base_request(
                        "preflight",
                        {
                            "test_overrides": {
                                "specify": {"available": True},
                                "metadata_status": status,
                            }
                        },
                    )
                )
                self.assertEqual(completed.returncode, 3)
                self.assert_response(response, "missing_prerequisite", 3)
                self.assertIn(code, [diag["code"] for diag in response["diagnostics"]])
                self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])

    def test_malformed_checksum_metadata_reports_incomplete(self) -> None:
        from speckit_pro_runner import runtime

        with tempfile.TemporaryDirectory() as tmp:
            plugin_root = Path(tmp) / "plugin"
            package_dir = plugin_root / "speckit_pro_runner"
            package_dir.mkdir(parents=True)
            (plugin_root / ".codex-plugin").mkdir()
            (plugin_root / ".codex-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
            (package_dir / "__init__.py").write_text("", encoding="utf-8")
            (package_dir / runtime.MANIFEST_NAME).write_text(
                json.dumps(
                    {
                        "runner_files": [
                            {
                                "path": {"value": "speckit_pro_runner/__init__.py"},
                                "sha256": hashlib.sha256(b"").hexdigest(),
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (package_dir / runtime.CHECKSUM_NAME).write_text("malformed-without-path\n", encoding="utf-8")

            report = runtime.metadata_report(plugin_root, package_dir, check_metadata=True, overrides={})

        self.assertEqual(report["verification_status"], "incomplete_metadata")

    def test_runbook_fixtures_have_non_claim_language(self) -> None:
        text = RUNBOOK_FILE.read_text(encoding="utf-8")
        self.assertIn("installed-cache launch proof", text)
        self.assertIn("public platform support", text)
        rows = []
        in_table = False
        for line in text.splitlines():
            if line.startswith("| fixture_id "):
                in_table = True
                continue
            if in_table and line.startswith("|---"):
                continue
            if in_table and line.startswith("|"):
                parts = [part.strip() for part in line.strip("|").split("|")]
                if len(parts) >= 10:
                    rows.append(parts)
        self.assertTrue(any(row[1] == "windows" and row[2] == "source_checkout" for row in rows))
        self.assertTrue(any(row[1] == "linux" and row[2] == "source_checkout" for row in rows))
        for row in rows:
            self.assertIn("XPLAT-007", row[9])
            self.assertNotIn("installed_cache", row[2])

    def test_no_cutover_or_public_claim_surfaces_changed(self) -> None:
        changed = changed_paths_against_review_base()
        status_by_path = changed_status_against_review_base()
        forbidden_exact = {
            "speckit-pro/.claude-plugin/plugin.json",
            "speckit-pro/.codex-plugin/plugin.json",
        }
        for path in changed:
            self.assertNotIn(path, forbidden_exact)
        forbidden_prefixes = (
            "dist/",
            "speckit-pro/skills/",
            "speckit-pro/codex-skills/",
            "speckit-pro/hooks/",
            "speckit-pro/codex-hooks",
            "docs-site/",
        )
        allowed_exact = {
            "dist/claude/speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh",
            "dist/claude/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py",
            "dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md",
            "dist/codex/speckit-pro/skills/speckit-autopilot/references/phase-execution-codex.md",
            "dist/codex/speckit-pro/skills/speckit-autopilot/references/task-list-canonical-codex.md",
            "dist/claude/speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh",
            "dist/codex/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py",
            "dist/codex/speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh",
            "dist/codex/speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh",
            "docs-site/scripts/validate-doc006-safe-aids.mjs",
            "docs-site/scripts/generate-reference-pages.mjs",
            "docs-site/src/data/safe-install-aids.ts",
            "docs-site/src/content/docs/reference/agents.md",
            "docs-site/src/content/docs/reference/scripts.md",
            "docs-site/src/content/docs/reference/skills.md",
            "docs-site/src/content/docs/reference/tests.md",
            "docs/ai/research/harness-knowledge-authority-inventory.md",
            "speckit-pro/codex-skills/speckit-autopilot/SKILL.md",
            "speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md",
            "speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md",
            "speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py",
            "speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh",
            "speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh",
        }
        allowed_xplat008_exact = {
            "docs-site/src/content/docs/contribute-and-release.md",
            "docs-site/src/content/docs/first-run.md",
            "docs-site/src/content/docs/install/claude-code.md",
            "docs-site/src/content/docs/install/codex.md",
            "docs-site/src/content/docs/security-and-trust.md",
            "docs-site/src/content/docs/troubleshooting.md",
            "docs-site/src/content/docs/update-and-rollback.md",
            "dist/claude/speckit-pro/README.md",
            "dist/claude/speckit-pro/hooks/hooks.json",
            "dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md",
            "dist/claude/speckit-pro/skills/speckit-install/SKILL.md",
            "dist/claude/speckit-pro/skills/speckit-scaffold-spec/SKILL.md",
            "dist/claude/speckit-pro/skills/speckit-status/SKILL.md",
            "dist/claude/speckit-pro/skills/speckit-upgrade/SKILL.md",
            "dist/codex/speckit-pro/README.md",
            "dist/codex/speckit-pro/codex-hooks.json",
            "dist/codex/speckit-pro/skills/install/SKILL.md",
            "dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md",
            "dist/codex/speckit-pro/skills/speckit-install/SKILL.md",
            "dist/codex/speckit-pro/skills/speckit-scaffold-spec/SKILL.md",
            "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
            "dist/codex/speckit-pro/skills/speckit-upgrade/SKILL.md",
            "dist/claude/speckit-pro/agents/gate-validator.md",
            "speckit-pro/codex-hooks.json",
            "speckit-pro/codex-skills/install/SKILL.md",
            "speckit-pro/codex-skills/speckit-autopilot/SKILL.md",
            "speckit-pro/codex-skills/speckit-install/SKILL.md",
            "speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md",
            "speckit-pro/codex-skills/speckit-status/SKILL.md",
            "speckit-pro/codex-skills/speckit-upgrade/SKILL.md",
            "speckit-pro/hooks/hooks.json",
            "speckit-pro/agents/gate-validator.md",
            "speckit-pro/skills/speckit-autopilot/SKILL.md",
            "speckit-pro/skills/speckit-install/SKILL.md",
            "speckit-pro/skills/speckit-scaffold-spec/SKILL.md",
            "speckit-pro/skills/speckit-status/SKILL.md",
            "speckit-pro/skills/speckit-upgrade/SKILL.md",
        }
        allowed_xplat008_prefixes = (
            "dist/claude/speckit-pro/speckit_pro_runner/",
            "dist/codex/speckit-pro/speckit_pro_runner/",
            "docs/ai/specs/.process/XPLAT-008",
        )
        allowed_xplat009_prefixes = (
            "dist/claude/speckit-pro/",
            "dist/codex/speckit-pro/",
            "speckit-pro/agents/",
            "speckit-pro/codex-agents/",
            "speckit-pro/codex-skills/",
            "speckit-pro/scripts/",
            "speckit-pro/skills/",
            "speckit-pro/speckit_pro_runner/",
            "docs/ai/specs/.process/XPLAT-009",
            "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/",
        )
        allowed_okf_prefixes = ("docs/ai/knowledge/",)
        allowed_tool_surface_exact = {
            # Operator-owned tool surface (tools: allowlist retirement):
            # capability-discovery role boundaries and the single-orchestrator
            # invariant moved to denial-based enforcement (disallowedTools);
            # dist mirrors rebuilt by scripts/build-plugin-payloads.py.
            "speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md",
            "speckit-pro/skills/speckit-autopilot/references/capability-discovery.md",
            "dist/claude/speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md",
            "dist/claude/speckit-pro/skills/speckit-autopilot/references/capability-discovery.md",
            "dist/codex/speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md",
            "dist/codex/speckit-pro/skills/speckit-autopilot/references/capability-discovery.md",
            "docs-site/src/content/docs/reference/source-vs-dist.md",
            "docs/ai/research/tool-agnostic-capability-discovery-spike.md",
        }
        for path in changed:
            if (
                path in allowed_exact
                or path in allowed_xplat008_exact
                or path in allowed_tool_surface_exact
            ):
                continue
            if path.startswith("dist/claude/speckit-pro/agents/") and path.endswith(".md"):
                source_agent = path.removeprefix("dist/claude/")
                dist_agent_path = REPO_ROOT / path
                source_agent_path = REPO_ROOT / source_agent
                self.assertNotEqual(status_by_path.get(path), "D", path)
                self.assertIn(source_agent, changed, path)
                self.assertTrue(source_agent_path.is_file(), source_agent)
                self.assertTrue(dist_agent_path.is_file(), path)
                self.assertEqual(
                    source_agent_path.read_text(encoding="utf-8"),
                    dist_agent_path.read_text(encoding="utf-8"),
                    path,
                )
                continue
            if path.startswith("dist/") and "/scripts/" in path and path.endswith(".sh"):
                self.assertEqual(status_by_path.get(path), "D", path)
                continue
            if path.startswith(allowed_xplat008_prefixes):
                continue
            if path.startswith(allowed_xplat009_prefixes):
                if path.endswith(".sh"):
                    self.assertEqual(status_by_path.get(path), "D", path)
                continue
            if path.startswith(allowed_okf_prefixes):
                continue
            self.assertFalse(path.startswith(forbidden_prefixes), path)
            if path.startswith("docs/"):
                self.assertTrue(
                    path.startswith("docs/ai/specs/")
                    or path.startswith("docs/prd-")
                    or path.startswith("docs/roadmap-"),
                    path,
                )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RunnerFoundationTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed
    print(f"test-speckit-pro-runner: {passed}/{total} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
