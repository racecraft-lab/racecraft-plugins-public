#!/usr/bin/env python3
"""Owner tests for the active-path guard package layout and its shared scan."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
sys.path.insert(0, str(PLUGIN_ROOT))
sys.path.insert(0, str(TEST_ROOT / "lib"))

from speckit_pro_runner.gates.active_path_guard import SourceFile, path_guard, runtime_guard, scan  # noqa: E402
from test_result import run_counted  # noqa: E402


class ActivePathGuardPolicyTests(unittest.TestCase):
    def test_active_path_guard_self_exemption_lists_exactly_its_modules(self) -> None:
        package_dir = REPO_ROOT / "speckit-pro/speckit_pro_runner/gates/active_path_guard"
        self.assertEqual(
            {f"speckit_pro_runner/gates/active_path_guard/{path.name}" for path in package_dir.glob("*.py")},
            set(runtime_guard.GUARD_SOURCE_PATHS),
        )

    def test_each_guard_policy_runs_through_the_shared_scan(self) -> None:
        sources = [
            SourceFile("scripts/helper.sh", "echo hi\n", "repo"),
            SourceFile("scripts/helper.ps1", "Write-Host hi\n", "repo"),
            SourceFile(".github/workflows/demo.yml", "jobs:\n  a:\n    steps:\n      - run: jq .version package.json\n", "repo"),
            SourceFile("speckit-pro/skills/demo/SKILL.md", "Run `jq .version plugin.json` to read it.\n", "repo"),
        ]
        cases = (
            {
                "policy": path_guard.PATH_GUARD_POLICY,
                "wrapper": path_guard.scan_sources,
                "scripts": [("scripts/helper.sh", "*.sh", ".sh file retained in scanned scope")],
                "jq": {".github/workflows/demo.yml": "blocking_active_gate", "speckit-pro/skills/demo/SKILL.md": "installed_runtime_cutover_surface"},
                "data": {"schema_version": "1.0", "blocking_count": 1},
                "absent": {"contract_id", "total_finding_count", "truncated_finding_count"},
                "code": "active_path_guard_blocked",
            },
            {
                "policy": runtime_guard.RUNTIME_GUARD_POLICY,
                "wrapper": runtime_guard.scan_installed_runtime_sources,
                "scripts": [
                    ("scripts/helper.sh", ".sh", "script file retained in scanned scope"),
                    ("scripts/helper.ps1", ".ps1", "script file retained in scanned scope"),
                ],
                "jq": {".github/workflows/demo.yml": "blocking_active_runtime", "speckit-pro/skills/demo/SKILL.md": "blocking_active_runtime"},
                "data": {"schema_version": "2.0", "contract_id": "installed-plugin-release", "blocking_count": 3, "total_finding_count": 5, "truncated_finding_count": 2},
                "absent": set(),
                "code": "active_runtime_guard_blocked",
            },
        )
        for case in cases:
            policy = case["policy"]
            with self.subTest(schema_version=policy.schema_version):
                findings = scan.scan_with_policy(policy, sources)
                self.assertEqual(findings, case["wrapper"](sources, REPO_ROOT))
                records = [finding.as_record() for finding in findings]
                self.assertEqual(
                    [(record["path"], record["pattern"], record["reason"]) for record in records if record["category"] == "script_file"],
                    case["scripts"],
                )
                self.assertEqual({record["path"]: record["classification"] for record in records if record["category"] == "jq"}, case["jq"])
                for record in records:
                    self.assertEqual(record["remediation"], scan.remediation(policy, record["classification"]))

                result = scan.policy_guard_response(
                    policy, SimpleNamespace(helper_id="active-path-guard"), SimpleNamespace(operation="guard", request_id="r"), findings
                )
                self.assertEqual(result["status"], "expected_failure")
                self.assertLessEqual(case["data"].items(), result["data"].items())
                self.assertFalse(case["absent"] & result["data"].keys())
                self.assertEqual([diag["code"] for diag in result["diagnostics"]], [case["code"]])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ActivePathGuardPolicyTests)
    raise SystemExit(run_counted(suite, label="test-active-path-guard-policy"))
