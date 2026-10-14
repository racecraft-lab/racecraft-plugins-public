#!/usr/bin/env python3
"""Scaffold identity through the public runner seam."""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from runner_invocation import run_runner  # noqa: E402
from host_skill_views import host_skill_root  # noqa: E402
from test_result import run_counted  # noqa: E402


INVALID_INPUTS = (
    {}, {"spec_id": "SPEC-001"},
    {"spec_id": "SPEC-001", "spec_name": None},
    {"spec_id": "SPEC-001", "spec_name": "!!!"},
    {"spec_id": "SPEC-001", "spec_name": "Save\x00Items"},
    {"spec_id": "SPEC-001", "spec_name": "Save Items", "branch_name": "override"},
    {"spec_id": "SPEC-01", "spec_name": "Save Items"},
    {"spec_id": "HRNS-15", "spec_name": "Save Items"},
    {"spec_id": "SPEC-006aa", "spec_name": "Save Items"},
    {"spec_id": "HRNS-015-old-branch", "spec_name": "Save Items"},
    {"spec_id": "006a", "spec_name": "Save Items"},
    {"spec_id": "HRNS1-015", "spec_name": "Save Items"},
)
IDENTITY_CASES = (
    ("SPEC-001", "Word Frequency JSON Output", "001-word-frequency-json-output"),
    ("SPEC-009", "Search & Database", "009-search-database"),
    ("SPEC-007", "  Café / JSON... Output!!  ", "007-cafe-json-output"),
    ("spec-042", "Save---Items_v2", "042-save-items-v2"),
    ("HRNS-015", "Autopilot Gate PR Emission Repair", "hrns-015-autopilot-gate-pr-emission-repair"),
    ("XPLAT-010", "Cross Host Scaffold", "xplat-010-cross-host-scaffold"),
    ("SPEC-006a", "UAT Skeleton", "006a-uat-skeleton"),
    ("hrns-015", "Harness Repair", "hrns-015-harness-repair"),
    ("EDA-001", "Attribution Foundation", "eda-001-attribution-foundation"),
    ("BRAND-001", "Racecraft Identity System", "brand-001-racecraft-identity-system"),
    ("FORMAL-002", "State Model", "formal-002-state-model"),
    ("PRSG-001", "Save Items", "prsg-001-save-items"),
    ("XPLAT-010A", "Cross Host Suffix", "xplat-010a-cross-host-suffix"),
    ("K-001", "Same Title", "k-001-same-title"),
    ("SPEC-001K", "Same Title", "001k-same-title"),
    ("SPEC-001", "Café 東京", "001-cafe"),
    ("SPEC-001", "A" * 300, "001-" + "a" * 300),
)


def assert_invalid_inputs(test: unittest.TestCase, inputs_grid: tuple[dict, ...], runner: str = "speckit-pro") -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for inputs in inputs_grid:
            with test.subTest(runner=runner, inputs=inputs):
                completed, result, _ = run_runner({
                    "schema_version": "1.0", "request_id": "invalid-scaffold-identity",
                    "helper_id": "derive-scaffold-branch", "operation": "derive-scaffold-branch",
                    "mode": "read_only", "inputs": inputs,
                }, cwd=root, extra_env={"PYTHONPATH": str(Path(__file__).resolve().parents[3] / runner)})
                test.assertEqual(result["status"], "input_error", result)
                test.assertNotEqual(completed.returncode, 0)
                test.assertEqual(result["data"]["verdict"], "stop")
                test.assertNotIn("branch_name", result["data"])
                test.assertEqual(list(root.iterdir()), [])


class ScaffoldIdentityTests(unittest.TestCase):
    def test_invalid_identity_fails_before_placement_or_writes(self) -> None:
        assert_invalid_inputs(self, INVALID_INPUTS)


class ScaffoldUnicodeIdentityTests(unittest.TestCase):
    def test_unicode_namespace_cannot_alias_an_ascii_identity(self) -> None:
        inputs = tuple({"spec_id": spec_id, "spec_name": "Same Title"} for spec_id in (
            "K-001", "KK-001", "KK-001", "KK-001", "SPEK-001", "K-001K",
        ))
        for runner in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            assert_invalid_inputs(self, inputs, runner)

    def test_unicode_number_suffix_cannot_alias_an_ascii_identity(self) -> None:
        inputs = tuple({"spec_id": spec_id, "spec_name": "Same Title"} for spec_id in (
            "SPEC-001K", "K-001K", "spec-001K",
        ))
        for runner in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            assert_invalid_inputs(self, inputs, runner)

    def test_non_ascii_controls_stop_before_placement(self) -> None:
        inputs = tuple({"spec_id": spec_id, "spec_name": "Same Title"} for spec_id in (
            "İ-001", "K-00١", "ſPEC-001", "ＳPEC-001", "SPEC-００１", "SPEC-001İ",
        ))
        for runner in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            assert_invalid_inputs(self, inputs, runner)


class ScaffoldHostContractTests(unittest.TestCase):
    def test_both_hosts_call_the_identity_helper_with_the_exact_roadmap_fields(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                text = (host_skill_root(host) / "speckit-scaffold-spec" / "SKILL.md").read_text(encoding="utf-8")
                row = re.search(r"\| `derive-scaffold-branch` \| `read_only` \| `([^`]+)` \|", text)
                self.assertIsNotNone(row, f"{host}: registered helper request is required")
                inputs = json.loads(row.group(1))
                self.assertEqual(inputs, {"spec_id": "<SPEC-ID>", "spec_name": "<exact roadmap spec name>"})
                for spec_id, title, expected in IDENTITY_CASES:
                    with self.subTest(spec_id=spec_id):
                        inputs.update(spec_id=spec_id, spec_name=title)
                        completed, result, _ = run_runner({
                            "schema_version": "1.0", "request_id": "scaffold-host-parity",
                            "helper_id": "derive-scaffold-branch", "operation": "derive-scaffold-branch",
                            "mode": "read_only", "inputs": inputs,
                        }, extra_env={"PYTHONPATH": str(Path(__file__).resolve().parents[3] / "dist" / host / "speckit-pro")})
                        self.assertEqual(completed.returncode, 0, result)
                        self.assertEqual(result["data"]["branch_name"], expected)
                step = text.split("### 2. Find the Spec in the Technical Roadmap", 1)[1].split("### 3.", 1)[0]
                self.assertIn("Run runner helper `derive-scaffold-branch`", step)
                self.assertIn("Use `data.branch_name` unchanged", step)
                self.assertNotIn("**Short name** for the branch", step)
                self.assertIn("verify its existing branch matches", step)


class ScaffoldBranchTests(unittest.TestCase):
    def test_roadmap_title_produces_the_canonical_numeric_branch(self) -> None:
        completed, result, diagnostics = run_runner({
            "schema_version": "1.0", "request_id": "scaffold-identity",
            "helper_id": "derive-scaffold-branch", "operation": "derive-scaffold-branch",
            "mode": "read_only",
            "inputs": {"spec_id": "SPEC-001", "spec_name": "Word Frequency JSON Output"},
        })
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(diagnostics, [])
        self.assertEqual(result["data"]["branch_name"], "001-word-frequency-json-output")

    def test_title_normalization_keeps_all_words_and_a_safe_single_segment(self) -> None:
        for spec_id, title, expected in IDENTITY_CASES:
            with self.subTest(spec_id=spec_id, title=title):
                completed, result, _ = run_runner({
                    "schema_version": "1.0", "request_id": "scaffold-normalization",
                    "helper_id": "derive-scaffold-branch", "operation": "derive-scaffold-branch",
                    "mode": "read_only", "inputs": {"spec_id": spec_id, "spec_name": title},
                })
                self.assertEqual(completed.returncode, 0, result)
                self.assertEqual(result["data"]["branch_name"], expected)
                self.assertRegex(result["data"]["branch_name"], r"^(?:[a-z]+-)?[0-9]{3}[a-z]?-[a-z0-9]+(?:-[a-z0-9]+)*$")


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-scaffold-identity"))
