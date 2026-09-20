#!/usr/bin/env python3
"""Owner tests for canonical native-evaluation catalog and grading contracts."""

from __future__ import annotations

import copy
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
sys.path.insert(0, str(TEST_ROOT / "lib"))

from native_eval_catalog import (  # noqa: E402
    NATIVE_SYNTHESIS_MECHANISMS,
    input_fingerprint,
    load_catalog,
    plan_trials,
    select_cases,
    validate_catalog,
)
from native_eval_grading import grade_observation  # noqa: E402
import native_eval_fixture_setup as fixture_setup  # noqa: E402
from native_eval_fixture_setup import materialize_workspace, populate_workspace  # noqa: E402
from test_result import run_counted  # noqa: E402


def case(checks: list[dict[str, object]] | None = None) -> dict[str, object]:
    return {
        "id": "native.selection",
        "layer": "trigger",
        "capability": "Select the declared skill and no sibling skill.",
        "timeout_seconds": 300,
        "resource_class": "ordinary",
        "requirements": [{"id": "r1", "description": "Selection is exact."}],
        "prompt": "Use {{skill}} for this request.",
        "fixtures": [{"source": "tests/speckit-pro/fixtures/input.txt", "destination": "input.txt"}],
        "hosts": {
            "claude": {"skill": "plugin:skill", "allowed_tools": ["Read"], "modes": ["plugin"]},
            "codex": {"skill": "skill", "allowed_tools": ["read_file"], "modes": ["project"]},
        },
        "checks": checks or [{
            "id": "selection", "requirement": "r1", "type": "selection",
            "expected": ["skill"], "allowed_extra": [],
        }],
        "native_differences": ["Adapters normalize native skill and tool aliases before grading."],
        "provenance": ["tests/speckit-pro/layer2-trigger/legacy-corpus.json"],
    }


def catalog(*cases: dict[str, object]) -> dict[str, object]:
    return {"schema_version": "native-eval-catalog/v1", "cases": list(cases)}


def pairing() -> dict[str, object]:
    return {
        "schema": "native-eval-pair/v1",
        "arms": {"claude": "plugin", "codex": "project"},
        "checks": [{
            "id": "pair", "requirement": "r1", "type": "comparison_plan",
            "expected_path": "tests/speckit-pro/pair-contract/expected-equivalence.json",
            "tolerance_path": "tests/speckit-pro/pair-contract/tolerance.json",
            "invariant_keys": [],
        }],
    }


def observation(**updates: object) -> dict[str, object]:
    value = {
        "completed": True,
        "error": None,
        "final_text": "done",
        "activations": ["skill"],
        "tool_calls": [],
        "artifacts": {},
        "usage": {},
    }
    value.update(updates)
    return value


def dispatch_check() -> dict[str, object]:
    return {
        "id": "round-one-routing", "requirement": "r1",
        "type": "native_subagent_dispatch",
        "expected": [
            {"item_id": "dispatch-i1", "role": "codebase-analyst"},
            {"item_id": "dispatch-i1", "role": "domain-researcher"},
        ],
        "forbidden_roles": ["spec-context-analyst", "consensus-synthesizer"],
    }


def git_final_state_check() -> dict[str, object]:
    return {
        "id": "final-git-boundary", "requirement": "r1",
        "type": "native_git_final_state", "head_equals_initial_feature": True,
        "branch": "feature", "commit_count": 0, "commits_added": [],
        "changed_tracked_paths_from_initial_feature": [],
        "status": {
            "clean": False, "tracked_dirty": False, "untracked_dirty": True,
            "tracked": [],
            "untracked": ["artifacts/parity-02-scaffold-guidance.md"],
        },
    }


def verification_pointer_check() -> dict[str, object]:
    return {
        "id": "verification-binding", "requirement": "r1",
        "type": "native_verification_pointer", "workflow_file": "workflow.md",
        "command_id": "INTEGRATION_TEST",
        "pointer_path": "specs/parity-01/.process/emission/verification-pointer.json",
        "reusable": False,
    }


def runner_result_check() -> dict[str, object]:
    return {
        "id": "runner-result", "requirement": "r1", "type": "native_runner_result",
        "request_path": "input.txt", "helper_id": "resolve-workflow-binding",
        "operation": "resolve-workflow-binding", "mode": "read_only",
        "expected_status": "expected_failure", "expected_exit_code": 1,
        "stdout_field_path": ["binding_status"],
        "expected_stdout_value": "ambiguous",
        "response_field_path": ["binding_result"],
    }


def _opaque_message(value: object) -> dict[str, object]:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    markers = re.findall(r"\[\[native-eval-item:([a-z0-9][a-z0-9._-]*)\]\]", value) \
        if isinstance(value, str) else []
    return {
        "observed_item_ids": markers[:64], "observed_marker_count": len(markers),
        "markers_truncated": len(markers) > 64,
        "message_sha256": hashlib.sha256(encoded).hexdigest(), "message_bytes": len(encoded),
    }


def dispatch_observation() -> dict[str, object]:
    roles = ("speckit-pro:codebase-analyst", "domain-researcher")
    calls = []
    attribution = []
    returns = []
    claude_results = []
    for index, role in enumerate(roles):
        identity = f"agent-{index}"
        prompt = "Inspect the item. [[native-eval-item:dispatch-i1]]"
        output = f"return-{index}"
        calls.append({
            "id": identity, "name": "subagent",
            "input": {"prompt": prompt, "subagent_type": role},
            "output": output, "success": True, "parent_id": None, "position": index,
        })
        attribution.append({
            "tool_call_index": index, "call_id": identity, **_opaque_message(prompt),
        })
        encoded = json.dumps(output, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf-8")
        returns.append({
            "tool_call_index": index, "call_id": identity,
            "authority": "claude-tool-result", "native_stream": "claude-main",
            "native_turn": None, "completion_index": index + 10,
            "content_sha256": hashlib.sha256(encoded).hexdigest(),
            "content_bytes": len(encoded), "content_nonempty": True,
        })
        claude_results.append({
            "tool_call_index": index, "id": identity,
            "tool_result_position": index + 10,
            "output_sha256": hashlib.sha256(encoded).hexdigest(),
            "output_bytes": len(encoded),
        })
    return observation(tool_calls=calls, native_metadata={
        "native_subagent_dispatch_attribution": {
            "schema": "native-subagent-dispatch-attribution/v1",
            "authority": "controller-bound-native-trace", "calls": attribution,
        },
        "subagent_return_order": {
            "schema": "native-subagent-return-order/v1", "scope": "direct-root-only",
            "returns": returns, "parent_file_changes": [],
        },
        "claude_tool_results": claude_results,
    })


class NativeEvalCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(cls.enterClassContext(tempfile.TemporaryDirectory()))
        fixture = cls.root / "tests" / "speckit-pro" / "fixtures" / "input.txt"
        fixture.parent.mkdir(parents=True)
        fixture.write_text("fixture\n", encoding="utf-8")
        (fixture.parent / "g3-request.json").write_text(
            json.dumps({
                "schema_version": "1.0", "request_id": "g3",
                "helper_id": "validate-gate", "operation": "validate-gate",
                "mode": "read_only", "inputs": {"gate": "G3"},
            }),
            encoding="utf-8",
        )
        (fixture.parent / "baseline.txt").write_text("baseline\n", encoding="utf-8")
        (fixture.parent / "feature.txt").write_text("feature\n", encoding="utf-8")
        pair_root = cls.root / "tests" / "speckit-pro" / "pair-contract"
        pair_root.mkdir(parents=True)
        (pair_root / "expected-equivalence.json").write_text(json.dumps({
            "schema": "speckit.layer7.expected-equivalence.v1",
            "fixture_id": "pair-contract",
            "description": "One exact normalized artifact.",
            "compare": [{"field": "result", "source": "result.txt", "tolerance_key": "result"}],
            "fail_fast": False,
            "report_format": "field-level-diff",
        }), encoding="utf-8")
        (pair_root / "tolerance.json").write_text(json.dumps({
            "schema": "speckit.layer7.tolerance.v1",
            "fixture_id": "pair-contract",
            "description": "Exact output contract.",
            "fields": {"result": {"tolerance": "exact", "rationale": "Results must match."}},
        }), encoding="utf-8")

    def assert_invalid(self, value: dict[str, object], text: str) -> None:
        with self.assertRaisesRegex(ValueError, text):
            validate_catalog(catalog(value), self.root)

    def test_loads_valid_strict_catalog(self) -> None:
        path = self.root / "catalog.json"
        path.write_text(json.dumps(catalog(case())), encoding="utf-8")
        loaded = load_catalog(path, self.root)
        self.assertEqual(loaded["schema_version"], "native-eval-catalog/v1")
        self.assertEqual(loaded["cases"][0]["id"], "native.selection")
        duplicate = self.root / "duplicate.json"
        duplicate.write_text('{"schema_version":"native-eval-catalog/v1","cases":[],"cases":[]}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            load_catalog(duplicate, self.root)

    def test_response_json_fields_require_complete_host_contracts(self) -> None:
        check = {
            "id": "native-sequence", "requirement": "r1", "type": "response_json_field",
            "field_path": ["steps", 0],
            "expected_by_host": {"claude": ["one"], "codex": ["one", "two"]},
        }
        validate_catalog(catalog(case([check])), self.root)
        for field_path in ([], [True], [-1], [1.0], [""]):
            with self.subTest(field_path=field_path):
                invalid = copy.deepcopy(check)
                invalid["field_path"] = field_path
                self.assert_invalid(case([invalid]), "field_path")
        for expected in ({}, {"claude": []}, {"claude": [], "codex": [], "other": []},
                         {"claude": float("nan"), "codex": []}):
            with self.subTest(expected=expected):
                invalid = copy.deepcopy(check)
                invalid["expected_by_host"] = expected
                self.assert_invalid(case([invalid]), "expected_by_host")

    def test_plan_repair_context_requires_sealed_fixtures_nested_runtime_and_strict_fields(self) -> None:
        check = {
            "id": "repair-context", "requirement": "r1",
            "type": "native_plan_repair_context",
            "contexts": {"original-prompt": "input.txt"},
            "g3_request_path": "g3-request.json",
            "executor_role": "phase-executor", "max_repairs": 2,
            "terminal_outcome": "pass",
        }
        value = case([check])
        value["resource_class"] = "nested"
        value["required_tools"] = ["specify"]
        value["fixtures"].append({
            "source": "tests/speckit-pro/fixtures/g3-request.json",
            "destination": "g3-request.json",
        })
        validated = validate_catalog(catalog(value), self.root)["cases"][0]
        self.assertEqual(validated["checks"][0], check)

        mutations = (
            ("contexts", {}, "contexts must contain 1 to 16 entries"),
            ("contexts", [], "contexts must contain 1 to 16 entries"),
            ("contexts", {f"context-{index}": "input.txt" for index in range(17)},
             "contexts must contain 1 to 16 entries"),
            ("contexts", {"Bad ID": "input.txt"}, "context id is not a stable identifier"),
            ("contexts", {"original": "../input.txt"}, "context path"),
            ("contexts", {"original": "missing.txt"}, "must reference declared fixtures"),
            ("g3_request_path", "../g3-request.json", "g3_request_path"),
            ("g3_request_path", "missing.json", "must reference declared fixtures"),
            ("executor_role", "speckit-pro:phase-executor", "executor_role is not a stable identifier"),
            ("max_repairs", 1, "max_repairs must be exactly 2"),
            ("max_repairs", True, "max_repairs must be exactly 2"),
            ("max_repairs", 2.0, "max_repairs must be exactly 2"),
            ("terminal_outcome", "complete", "terminal_outcome must be pass or unresolved"),
            ("terminal_outcome", [], "terminal_outcome must be pass or unresolved"),
        )
        for field, replacement, message in mutations:
            with self.subTest(field=field, replacement=replacement):
                malformed = copy.deepcopy(value)
                malformed["checks"][0][field] = replacement
                self.assert_invalid(malformed, message)

        extra = copy.deepcopy(value)
        extra["checks"][0]["unexpected"] = True
        self.assert_invalid(extra, "malformed parameters")
        missing = copy.deepcopy(value)
        del missing["checks"][0]["contexts"]
        self.assert_invalid(missing, "malformed parameters")

        ordinary = copy.deepcopy(value)
        ordinary["resource_class"] = "ordinary"
        self.assert_invalid(ordinary, "requires nested resource_class")
        no_toolchain = copy.deepcopy(value)
        del no_toolchain["required_tools"]
        self.assert_invalid(no_toolchain, "requires required_tools.*specify")

    def test_rejects_empty_malformed_duplicate_and_host_gap_catalogs(self) -> None:
        with self.assertRaisesRegex(ValueError, "nonempty"):
            validate_catalog(catalog(), self.root)
        malformed = case()
        malformed["extra"] = True
        self.assert_invalid(malformed, "malformed case")
        duplicate = case()
        with self.assertRaisesRegex(ValueError, "duplicate case ids"):
            validate_catalog(catalog(case(), duplicate), self.root)
        missing_host = case()
        del missing_host["hosts"]["codex"]
        self.assert_invalid(missing_host, "exactly claude and codex")
        extra_host = case()
        extra_host["hosts"]["other"] = copy.deepcopy(extra_host["hosts"]["claude"])
        self.assert_invalid(extra_host, "exactly claude and codex")

    def test_requires_bounded_timeout_and_known_resource_class(self) -> None:
        for timeout in (0, 3601, True, 1.5):
            malformed = case()
            malformed["timeout_seconds"] = timeout
            self.assert_invalid(malformed, "timeout_seconds must be an integer from 1 through 3600")
        for resource_class in ("", "teams", None, True):
            malformed = case()
            malformed["resource_class"] = resource_class
            self.assert_invalid(malformed, "unknown resource_class")
        nested = case()
        nested["timeout_seconds"] = 3600
        nested["resource_class"] = "nested"
        self.assertEqual(validate_catalog(catalog(nested), self.root)["cases"][0]["resource_class"], "nested")

    def test_required_tools_are_optional_unique_and_strictly_known(self) -> None:
        absent = case()
        self.assertNotIn("required_tools", validate_catalog(catalog(absent), self.root)["cases"][0])

        specified = case()
        specified["required_tools"] = ["specify"]
        self.assertEqual(
            validate_catalog(catalog(specified), self.root)["cases"][0]["required_tools"],
            ["specify"],
        )
        for value, message in (
            ([], "required_tools must be nonempty"),
            (["specify", "specify"], "required_tools contains duplicates"),
            (["uv"], "unsupported required tool"),
            ("specify", "required_tools must be a list"),
        ):
            with self.subTest(value=value):
                malformed = case()
                malformed["required_tools"] = value
                self.assert_invalid(malformed, message)

    def test_git_metadata_write_is_explicit_and_requires_a_git_fixture(self) -> None:
        valid = case()
        valid["git_fixture"] = {
            "recipe": fixture_setup.GIT_FIXTURE_RECIPE,
            "baseline": [{
                "source": "tests/speckit-pro/fixtures/baseline.txt",
                "destination": "baseline.txt",
            }],
        }
        valid["git_metadata_access"] = "write"
        loaded = validate_catalog(catalog(valid), self.root)["cases"][0]
        self.assertEqual(loaded["git_metadata_access"], "write")

        missing_fixture = case()
        missing_fixture["git_metadata_access"] = "write"
        self.assert_invalid(missing_fixture, "git_metadata_access requires git_fixture")
        for value in ("read", "deny", True, None):
            malformed = copy.deepcopy(valid)
            malformed["git_metadata_access"] = value
            self.assert_invalid(malformed, "git_metadata_access must be write")

    def test_requires_pairing_only_for_parity_and_keeps_host_checks_independent(self) -> None:
        missing = case()
        missing["layer"] = "parity"
        self.assert_invalid(missing, "parity case must define pairing")
        forbidden = case()
        forbidden["pairing"] = pairing()
        self.assert_invalid(forbidden, "forbidden outside parity")
        valid = case()
        valid["layer"] = "parity"
        valid["pairing"] = pairing()
        self.assertEqual(validate_catalog(catalog(valid), self.root)["cases"][0]["layer"], "parity")
        cross_host = copy.deepcopy(valid)
        cross_host["checks"] = [{
            "id": "judge", "requirement": "r1", "type": "semantic",
            "rubric": "Compare both native host observations for equivalent results.",
        }]
        self.assert_invalid(cross_host, "per-host semantic check requires cross-host evidence")
        wrong_mode = copy.deepcopy(valid)
        wrong_mode["pairing"]["arms"]["codex"] = "missing"
        self.assert_invalid(wrong_mode, "mode is not declared")

    def test_rejects_empty_and_uncovered_requirements_and_duplicate_ids(self) -> None:
        empty = case()
        empty["requirements"] = []
        self.assert_invalid(empty, "no requirements")
        uncovered = case()
        uncovered["requirements"].append({"id": "r2", "description": "Another contract."})
        self.assert_invalid(uncovered, "uncovered requirements")
        duplicate_requirement = case()
        duplicate_requirement["requirements"].append({"id": "r1", "description": "Duplicate."})
        self.assert_invalid(duplicate_requirement, "duplicate requirement ids")
        duplicate_check = case()
        duplicate_check["checks"].append(copy.deepcopy(duplicate_check["checks"][0]))
        self.assert_invalid(duplicate_check, "duplicate check ids")
        no_checks = case()
        no_checks["checks"] = []
        self.assert_invalid(no_checks, "no checks")
        no_provenance = case()
        no_provenance["provenance"] = []
        self.assert_invalid(no_provenance, "provenance must be nonempty")
        no_modes = case()
        no_modes["hosts"]["claude"]["modes"] = []
        self.assert_invalid(no_modes, "modes must be nonempty")

    def test_rejects_path_traversal_missing_sources_and_symlink_escape(self) -> None:
        traversal = case()
        traversal["fixtures"][0]["source"] = "tests/speckit-pro/../secret.txt"
        self.assert_invalid(traversal, "canonical relative path")
        destination = case()
        destination["fixtures"][0]["destination"] = "../outside.txt"
        self.assert_invalid(destination, "canonical relative path")
        missing = case()
        missing["fixtures"][0]["source"] = "tests/speckit-pro/fixtures/missing.txt"
        self.assert_invalid(missing, "source is missing")
        outside = self.root / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        link = self.root / "tests" / "speckit-pro" / "fixtures" / "escape.txt"
        try:
            os.symlink(outside, link)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        escaped = case()
        escaped["fixtures"][0]["source"] = "tests/speckit-pro/fixtures/escape.txt"
        self.assert_invalid(escaped, "escaped tests/speckit-pro")

    def test_rejects_duplicate_and_overlapping_fixture_destinations(self) -> None:
        duplicate = case()
        duplicate["fixtures"].append(copy.deepcopy(duplicate["fixtures"][0]))
        self.assert_invalid(duplicate, "duplicate fixture destinations")
        overlapping = case()
        child = copy.deepcopy(overlapping["fixtures"][0])
        child["destination"] = "input.txt/child.txt"
        overlapping["fixtures"].append(child)
        self.assert_invalid(overlapping, "overlapping fixture destinations")
        siblings = case()
        sibling = copy.deepcopy(siblings["fixtures"][0])
        sibling["destination"] = "other/input.txt"
        siblings["fixtures"].append(sibling)
        self.assertEqual(len(validate_catalog(catalog(siblings), self.root)["cases"][0]["fixtures"]), 2)

    def test_git_fixture_recipe_is_fixed_and_baseline_is_confined(self) -> None:
        valid = case()
        valid["git_fixture"] = {
            "recipe": "baseline-feature-origin-main/v1",
            "baseline": [{
                "source": "tests/speckit-pro/fixtures/baseline.txt", "destination": "input.txt",
            }],
        }
        self.assertEqual(
            validate_catalog(catalog(valid), self.root)["cases"][0]["git_fixture"]["recipe"],
            "baseline-feature-origin-main/v1",
        )
        for malformed, message in (
            ({"recipe": "other", "baseline": valid["git_fixture"]["baseline"]}, "unsupported git fixture recipe"),
            ({"recipe": "baseline-feature-origin-main/v1", "baseline": []}, "baseline must be nonempty"),
            ({"recipe": "baseline-feature-origin-main/v1", "baseline": valid["git_fixture"]["baseline"], "branch": "other"}, "malformed git_fixture"),
            ({"recipe": "baseline-feature-origin-main/v1", "baseline": [{
                "source": "tests/speckit-pro/fixtures/baseline.txt", "destination": ".git/config",
            }]}, "cannot target a reserved runtime path"),
            ({"recipe": "baseline-feature-origin-main/v1", "baseline": [{
                "source": "tests/speckit-pro/fixtures/baseline.txt", "destination": ".AgEnTs/config",
            }]}, "cannot target a reserved runtime path"),
        ):
            candidate = case()
            candidate["git_fixture"] = malformed
            self.assert_invalid(candidate, message)
        feature_control_path = copy.deepcopy(valid)
        feature_control_path["fixtures"][0]["destination"] = ".CoDeX/config"
        self.assert_invalid(feature_control_path, "cannot target a reserved runtime path")

    def test_git_fixture_registered_worktree_topology_is_strict_and_confined(self) -> None:
        valid = case()
        valid["git_fixture"] = {
            "recipe": "baseline-feature-origin-main/v1",
            "baseline": [{
                "source": "tests/speckit-pro/fixtures/baseline.txt", "destination": "input.txt",
            }],
            "worktrees": [
                {"path": ".worktrees/base", "branch": "scenario/base", "revision": "baseline"},
                {"path": ".worktrees/work", "branch": "scenario/work", "revision": "feature"},
            ],
        }
        accepted = validate_catalog(catalog(valid), self.root)["cases"][0]
        self.assertEqual(accepted["git_fixture"]["worktrees"], valid["git_fixture"]["worktrees"])

        for rows, message in (
            ([], "one to four"),
            ([valid["git_fixture"]["worktrees"][0]] * 2, "duplicate path or branch"),
            ([{"path": "../outside", "branch": "scenario/a", "revision": "feature"}],
             "confined .worktrees child"),
            ([{"path": ".worktrees/a", "branch": "main", "revision": "feature"}],
             "scenario branch"),
            ([{"path": ".worktrees/a", "branch": "scenario/a", "revision": "HEAD"}],
             "baseline or feature"),
        ):
            candidate = copy.deepcopy(valid)
            candidate["git_fixture"]["worktrees"] = rows
            self.assert_invalid(candidate, message)

        reserved = copy.deepcopy(valid)
        reserved["fixtures"][0]["destination"] = ".worktrees/owned.txt"
        self.assert_invalid(reserved, "reserve the .worktrees directory")

    def test_native_git_final_state_requires_git_fixture_and_strict_consistent_fields(self) -> None:
        valid = case([git_final_state_check()])
        valid["git_fixture"] = {
            "recipe": "baseline-feature-origin-main/v1",
            "baseline": [{
                "source": "tests/speckit-pro/fixtures/baseline.txt",
                "destination": "input.txt",
            }],
        }
        accepted = validate_catalog(catalog(valid), self.root)["cases"][0]["checks"][0]
        self.assertEqual(accepted["status"]["untracked"], [
            "artifacts/parity-02-scaffold-guidance.md",
        ])

        self.assert_invalid(case([git_final_state_check()]), "requires git_fixture")
        variants = []
        for field, value, message in (
            ("head_equals_initial_feature", 1, "must be boolean"),
            ("commit_count", True, "nonnegative integer"),
            ("branch", "", "nonempty text"),
        ):
            malformed = copy.deepcopy(valid)
            malformed["checks"][0][field] = value
            variants.append((malformed, message))
        contradictory_count = copy.deepcopy(valid)
        contradictory_count["checks"][0]["commit_count"] = 1
        variants.append((contradictory_count, "does not match commits_added"))
        contradictory_status = copy.deepcopy(valid)
        contradictory_status["checks"][0]["status"]["clean"] = True
        variants.append((contradictory_status, "summary is inconsistent"))
        non_boolean_status = copy.deepcopy(valid)
        non_boolean_status["checks"][0]["status"]["tracked_dirty"] = 0
        variants.append((non_boolean_status, "booleans are malformed"))
        duplicate_path = copy.deepcopy(valid)
        duplicate_path["checks"][0]["status"]["untracked"] *= 2
        variants.append((duplicate_path, "sorted and unique"))
        for malformed, message in variants:
            with self.subTest(message=message):
                self.assert_invalid(malformed, message)

    def test_native_verification_pointer_has_one_strict_canonical_contract(self) -> None:
        valid = case([verification_pointer_check()])
        accepted = validate_catalog(catalog(valid), self.root)["cases"][0]["checks"][0]
        self.assertEqual(accepted["command_id"], "INTEGRATION_TEST")
        for field, value, message in (
            ("workflow_file", "../workflow.md", "workflow_file is malformed"),
            ("pointer_path", "/tmp/pointer.json", "pointer_path is malformed"),
            ("command_id", "integration-test", "command_id is malformed"),
            ("reusable", 0, "reusable must be boolean"),
        ):
            malformed = copy.deepcopy(valid)
            malformed["checks"][0][field] = value
            with self.subTest(field=field):
                self.assert_invalid(malformed, message)
        duplicate = case([verification_pointer_check(), {
            **verification_pointer_check(), "id": "verification-binding-two",
        }])
        self.assert_invalid(duplicate, "ambiguous native verification pointer checks")

    def test_native_runner_result_has_one_staged_strict_contract(self) -> None:
        valid = case([runner_result_check()])
        accepted = validate_catalog(catalog(valid), self.root)["cases"][0]["checks"][0]
        self.assertEqual(accepted["expected_status"], "expected_failure")
        for field, value, message in (
            ("request_path", "../request.json", "request_path is malformed"),
            ("helper_id", "Resolve Binding", "helper_id is malformed"),
            ("mode", "apply", "mode must be read_only"),
            ("expected_exit_code", True, "contradicts expected_status"),
            ("stdout_field_path", [], "stdout_field_path is malformed"),
            ("response_field_path", [""], "response_field_path is malformed"),
        ):
            malformed = copy.deepcopy(valid)
            malformed["checks"][0][field] = value
            with self.subTest(field=field):
                self.assert_invalid(malformed, message)
        unstaged = copy.deepcopy(valid)
        unstaged["checks"][0]["request_path"] = "missing/request.json"
        self.assert_invalid(unstaged, "must reference a declared fixture")
        duplicate = case([runner_result_check(), {
            **runner_result_check(), "id": "runner-result-two",
        }])
        self.assert_invalid(duplicate, "ambiguous native runner result checks")


    def test_rejects_unknown_checks_empty_rubrics_and_bad_templates(self) -> None:
        unknown = case()
        unknown["checks"][0]["type"] = "equality"
        self.assert_invalid(unknown, "unknown type")
        semantic = case([{"id": "judge", "requirement": "r1", "type": "semantic", "rubric": ""}])
        self.assert_invalid(semantic, "rubric must be nonempty")
        bad_regex = case([{
            "id": "text", "requirement": "r1", "type": "text",
            "source": "final_text", "pattern": "[",
        }])
        self.assert_invalid(bad_regex, "not a valid regular expression")
        bad_prompt = case()
        bad_prompt["prompt"] = "Use {{provider}}."
        self.assert_invalid(bad_prompt, "unsupported placeholder")
        unresolved_python = case()
        unresolved_python["prompt"] = "Run {{resolved_python}} -m speckit_pro_runner."
        self.assert_invalid(unresolved_python, "unsupported placeholder")
        resolved_python = case()
        resolved_python["required_tools"] = ["specify"]
        resolved_python["prompt"] = "Run {{resolved_python}} -m speckit_pro_runner."
        validate_catalog(catalog(resolved_python), self.root)
        null_skill = case()
        null_skill["hosts"]["codex"]["skill"] = None
        self.assert_invalid(null_skill, "cannot interpolate a null host skill")
        malformed_parameters = case()
        malformed_parameters["checks"][0]["unexpected"] = True
        self.assert_invalid(malformed_parameters, "malformed parameters")

    def test_json_field_alternatives_are_optional_nonempty_strict_json_values(self) -> None:
        check = {
            "id": "decision", "requirement": "r1", "type": "json_field",
            "path": "result.json", "field_path": ["decision"], "expected": "majority",
        }
        absent = case([copy.deepcopy(check)])
        self.assertNotIn(
            "alternatives",
            validate_catalog(catalog(absent), self.root)["cases"][0]["checks"][0],
        )
        with_alternatives = case([{**check, "alternatives": ["unanimous", 3, {"votes": [2, 1]}]}])
        self.assertEqual(
            validate_catalog(catalog(with_alternatives), self.root)["cases"][0]["checks"][0]["alternatives"],
            ["unanimous", 3, {"votes": [2, 1]}],
        )
        for alternatives, message in (
            ([], "alternatives must be a nonempty list"),
            ("unanimous", "alternatives must be a nonempty list"),
            ([float("nan")], r"alternatives\[0\] must be a strict JSON value"),
            ([{"votes": object()}], r"alternatives\[0\] must be a strict JSON value"),
        ):
            with self.subTest(alternatives=alternatives):
                malformed = case([{**check, "alternatives": alternatives}])
                self.assert_invalid(malformed, message)

    def test_file_access_check_requires_one_exact_read_file_path(self) -> None:
        valid = case([{
            "id": "read-plan", "requirement": "r1", "type": "file_access",
            "operation": "read_file", "path": "docs/plan.md",
        }])
        self.assertEqual(
            validate_catalog(catalog(valid), self.root)["cases"][0]["checks"][0]["path"],
            "docs/plan.md",
        )
        for updates, message in (
            ({"operation": "search_files"}, "operation must be read_file"),
            ({"path": "../plan.md"}, "canonical relative path"),
            ({"path": "/tmp/plan.md"}, "must be relative"),
            ({"extra": True}, "malformed parameters"),
        ):
            with self.subTest(updates=updates):
                malformed = copy.deepcopy(valid)
                malformed["checks"][0].update(updates)
                self.assert_invalid(malformed, message)
        missing = copy.deepcopy(valid)
        del missing["checks"][0]["path"]
        self.assert_invalid(missing, "malformed parameters")

    def test_file_search_requires_complete_canonical_match_contract(self) -> None:
        check = {
            "id": "search", "requirement": "r1", "type": "file_search",
            "pattern": "**/*roadmap*.md", "matches": ["docs/current-technical-roadmap.md"],
        }
        self.assertEqual(
            validate_catalog(catalog(case([check])), self.root)["cases"][0]["checks"][0],
            check,
        )
        validate_catalog(catalog(case([{**check, "matches": []}])), self.root)
        for updates, message in (
            ({"pattern": "*roadmap*.md"}, "recursive basename glob"),
            ({"pattern": "**/docs/*.md"}, "recursive basename glob"),
            ({"matches": None}, "matches must be a list"),
            ({"matches": ["../roadmap.md"]}, "canonical relative path"),
            ({"matches": ["file.txt"]}, "must satisfy its pattern"),
            ({"matches": ["roadmap.md", "roadmap.md"]}, "must be unique"),
            ({"ignored_paths": ["docs"]}, "malformed parameters"),
        ):
            with self.subTest(updates=updates):
                self.assert_invalid(case([{**check, **updates}]), message)

    def test_tool_used_include_failed_is_an_optional_strict_boolean(self) -> None:
        base = {
            "id": "forbidden", "requirement": "r1", "type": "tool_used",
            "name": "Write", "min": 0, "max": 0,
        }
        for include_failed in (None, False, True):
            with self.subTest(include_failed=include_failed):
                check = copy.deepcopy(base)
                if include_failed is not None:
                    check["include_failed"] = include_failed
                self.assertEqual(
                    validate_catalog(catalog(case([check])), self.root)["cases"][0]["checks"][0],
                    check,
                )
        for include_failed in ("true", 1, 0, [], {}):
            with self.subTest(include_failed=include_failed):
                check = copy.deepcopy(base)
                check["include_failed"] = include_failed
                self.assert_invalid(case([check]), "include_failed must be boolean")

    def test_native_subagent_dispatch_requires_exact_pairs_and_nested_runtime(self) -> None:
        valid = case([dispatch_check()])
        valid["resource_class"] = "nested"
        loaded = validate_catalog(catalog(valid), self.root)["cases"][0]["checks"][0]
        self.assertEqual(loaded, dispatch_check())

        mutations = []
        ordinary = copy.deepcopy(valid)
        ordinary["resource_class"] = "ordinary"
        mutations.append((ordinary, "requires nested resource_class"))
        for field, value, message in (
            ("expected", [], "expected must be nonempty"),
            ("expected", [{"item_id": "dispatch-i1", "role": "codebase-analyst"}] * 2,
             "expected contains duplicates"),
            ("expected", [{"item_id": "bad item", "role": "codebase-analyst"}],
             "item_id is not a stable identifier"),
            ("expected", [{"item_id": "dispatch-i1", "role": "codebase-analyst", "extra": True}],
             "expected item is malformed"),
            ("forbidden_roles", ["codebase-analyst"], "overlap expected roles"),
            ("forbidden_roles", ["spec-context-analyst", "spec-context-analyst"],
             "forbidden_roles contains duplicates"),
        ):
            malformed = copy.deepcopy(valid)
            malformed["checks"][0][field] = value
            mutations.append((malformed, message))
        for malformed, message in mutations:
            with self.subTest(message=message):
                self.assert_invalid(malformed, message)

    def test_subagent_return_check_requires_one_canonical_path(self) -> None:
        valid = case([{
            "id": "worker-return", "requirement": "r1",
            "type": "subagent_returns_before_parent_file_change",
            "path": "artifacts/post-implementation-report.md",
        }])
        self.assertEqual(
            validate_catalog(catalog(valid), self.root)["cases"][0]["checks"][0]["path"],
            "artifacts/post-implementation-report.md",
        )
        for updates, message in (({"path": "../report.md"}, "canonical relative path"),
                                 ({"unexpected": True}, "malformed parameters")):
            malformed = copy.deepcopy(valid)
            malformed["checks"][0].update(updates)
            self.assert_invalid(malformed, message)
        missing = copy.deepcopy(valid)
        del missing["checks"][0]["path"]
        self.assert_invalid(missing, "malformed parameters")

    def test_native_synthesis_mechanism_requires_exact_host_plan_and_declared_evidence(self) -> None:
        mechanism = {
            "id": "mechanism", "requirement": "r1", "type": "native_synthesis_mechanism",
            "artifact_path": "scenario-output/consensus-result.json",
            "per_host": {
                "claude": {
                    "mode": "dedicated_subagent",
                    "role": "speckit-pro:consensus-synthesizer",
                },
                "codex": {"mode": "dedicated_subagent", "role": "consensus-synthesizer"},
            },
        }
        checks = [
            mechanism,
            {
                "id": "source-a", "requirement": "r1", "type": "file_access",
                "operation": "read_file", "path": "scenario-inputs/analyst-a.md",
            },
            {
                "id": "artifact", "requirement": "r1", "type": "file_exists",
                "path": "scenario-output/consensus-result.json", "exists": True,
            },
        ]
        valid = case(checks)
        loaded = validate_catalog(catalog(valid), self.root)["cases"][0]["checks"][0]
        self.assertEqual(loaded["per_host"]["codex"]["mode"], "dedicated_subagent")

        mutations = (
            (lambda check: check.update(artifact_path="../result.json"), "canonical relative path"),
            (lambda check: check["per_host"].pop("codex"), "exactly claude and codex"),
            (lambda check: check["per_host"].update(other={"mode": "parent_session", "role": None}),
             "exactly claude and codex"),
            (lambda check: check["per_host"]["claude"].update(mode="parent_session"),
             "claude mode must be dedicated_subagent"),
            (lambda check: check["per_host"]["claude"].update(role="consensus-synthesizer"),
             "claude role must be speckit-pro:consensus-synthesizer"),
            (lambda check: check["per_host"]["codex"].update(mode="parent_session"),
             "codex mode must be dedicated_subagent"),
            (lambda check: check["per_host"]["codex"].update(role=None),
             "codex role must be consensus-synthesizer"),
            (lambda check: check["per_host"]["codex"].update(extra=True), "malformed codex settings"),
        )
        for mutate, message in mutations:
            with self.subTest(message=message):
                malformed = copy.deepcopy(valid)
                mutate(malformed["checks"][0])
                self.assert_invalid(malformed, message)

        undeclared = copy.deepcopy(valid)
        undeclared["checks"][-1]["path"] = "other.json"
        self.assert_invalid(undeclared, "artifact_path must be declared")
        unread = copy.deepcopy(valid)
        unread["checks"].pop(1)
        self.assert_invalid(unread, "requires at least one file_access")

    def test_selects_in_catalog_order_and_rejects_unknown_or_empty_filters(self) -> None:
        second = case()
        second["id"] = "native.functional"
        second["layer"] = "functional"
        value = catalog(case(), second)
        self.assertEqual([row["id"] for row in select_cases(value, layers=["functional"])], ["native.functional"])
        self.assertEqual([row["id"] for row in select_cases(value, case_ids=["native.selection"])], ["native.selection"])
        with self.assertRaisesRegex(ValueError, "unknown"):
            select_cases(value, layers=["parity"])
        with self.assertRaisesRegex(ValueError, "unknown"):
            select_cases(value, case_ids=["missing"])
        with self.assertRaisesRegex(ValueError, "nonempty"):
            select_cases(value, layers=[])
        with self.assertRaisesRegex(ValueError, "selected no cases"):
            select_cases(value, layers=["functional"], case_ids=["native.selection"])

    def test_plans_every_host_mode_and_one_based_trial_deterministically(self) -> None:
        value = case()
        value["hosts"]["claude"]["modes"] = ["plugin", "source"]
        rows = plan_trials([value])
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0], {"case_id": "native.selection", "host": "claude", "mode": "plugin", "trial": 1})
        self.assertEqual(rows[-1], {"case_id": "native.selection", "host": "codex", "mode": "project", "trial": 1})
        repeated = plan_trials([value], hosts=("codex",), runs=3)
        self.assertEqual([row["trial"] for row in repeated], [1, 2, 3])
        missing = case()
        del missing["hosts"]["codex"]
        with self.assertRaisesRegex(ValueError, "does not support"):
            plan_trials([missing])
        for invalid in (0, 51, True):
            with self.assertRaisesRegex(ValueError, "1 through 50"):
                plan_trials([value], runs=invalid)

    def test_fingerprint_binds_all_inputs_but_not_a_grader(self) -> None:
        value = case()
        original = input_fingerprint(value, "claude", "plugin", {"model": "sonnet", "cli": "1"})
        self.assertRegex(original, r"^[0-9a-f]{64}$")
        changed_case = copy.deepcopy(value)
        changed_case["prompt"] = "Changed {{skill}} prompt."
        self.assertNotEqual(original, input_fingerprint(changed_case, "claude", "plugin", {"model": "sonnet", "cli": "1"}))
        self.assertNotEqual(original, input_fingerprint(value, "claude", "plugin", {"model": "sonnet", "cli": "2"}))
        regraded = copy.deepcopy(value)
        regraded["checks"][0]["expected"] = ["different-required-outcome"]
        self.assertEqual(original, input_fingerprint(regraded, "claude", "plugin", {"model": "sonnet", "cli": "1"}))
        tool_required = copy.deepcopy(value)
        tool_required["required_tools"] = ["specify"]
        self.assertNotEqual(
            original,
            input_fingerprint(tool_required, "claude", "plugin", {"model": "sonnet", "cli": "1"}),
        )
        git_metadata_write = copy.deepcopy(value)
        git_metadata_write["git_metadata_access"] = "write"
        self.assertNotEqual(
            original,
            input_fingerprint(
                git_metadata_write, "claude", "plugin", {"model": "sonnet", "cli": "1"},
            ),
        )
        with self.assertRaisesRegex(ValueError, "runtime_identity"):
            input_fingerprint(value, "claude", "plugin", {})
        with self.assertRaisesRegex(ValueError, "mode"):
            input_fingerprint(value, "claude", "unknown", "runtime")


class NativeEvalGradingTests(unittest.TestCase):
    def test_direct_grading_rejects_incomplete_or_ambiguous_contracts(self) -> None:
        valid = case()
        self.assertEqual(grade_observation(valid, observation())["status"], "pass")
        variants = [
            ("uncovered", "requirements", valid["requirements"] + [{"id": "r2", "description": "Must not disappear."}]),
            ("duplicate-requirement", "requirements", valid["requirements"] * 2),
            ("duplicate-check", "checks", valid["checks"] * 2),
            ("missing-requirements", "requirements", None),
            ("non-list-requirements", "requirements", {"r1": "selection"}),
            ("malformed-requirement", "requirements", [*valid["requirements"], None]),
            ("missing-checks", "checks", None),
            ("non-list-checks", "checks", 1),
        ]
        for label, field, value in variants:
            with self.subTest(label=label):
                malformed = copy.deepcopy(valid)
                malformed[field] = value
                self.assertEqual(grade_observation(malformed, observation())["status"], "invalid")

    def test_native_subagent_dispatch_exactness_and_one_mutation_controls(self) -> None:
        value = case([dispatch_check()])
        value["resource_class"] = "nested"
        valid = dispatch_observation()
        self.assertEqual(grade_observation(value, valid, host="claude")["status"], "pass")
        self.assertEqual(grade_observation(value, valid)["status"], "invalid")

        def remove_call(evidence, index):
            evidence["tool_calls"].pop(index)
            metadata = evidence["native_metadata"]
            metadata["native_subagent_dispatch_attribution"]["calls"].pop(index)
            metadata["subagent_return_order"]["returns"].pop(index)
            metadata["claude_tool_results"].pop(index)
            for new_index, item in enumerate(
                metadata["native_subagent_dispatch_attribution"]["calls"]
            ):
                item["tool_call_index"] = new_index
            for new_index, item in enumerate(metadata["subagent_return_order"]["returns"]):
                item["tool_call_index"] = new_index

        variants = []
        missing = copy.deepcopy(valid)
        remove_call(missing, 1)
        variants.append(("missing", missing, "fail"))
        duplicate = copy.deepcopy(valid)
        extra_call = copy.deepcopy(duplicate["tool_calls"][0])
        extra_call.update({"id": "agent-extra", "position": 2})
        duplicate["tool_calls"].append(extra_call)
        extra_attr = copy.deepcopy(
            duplicate["native_metadata"]["native_subagent_dispatch_attribution"]["calls"][0]
        )
        extra_attr.update({"tool_call_index": 2, "call_id": "agent-extra"})
        duplicate["native_metadata"]["native_subagent_dispatch_attribution"]["calls"].append(extra_attr)
        extra_return = copy.deepcopy(duplicate["native_metadata"]["subagent_return_order"]["returns"][0])
        extra_return.update({"tool_call_index": 2, "call_id": "agent-extra"})
        duplicate["native_metadata"]["subagent_return_order"]["returns"].append(extra_return)
        extra_result = copy.deepcopy(duplicate["native_metadata"]["claude_tool_results"][0])
        extra_result.update({"tool_call_index": 2, "id": "agent-extra"})
        duplicate["native_metadata"]["claude_tool_results"].append(extra_result)
        variants.append(("duplicate", duplicate, "fail"))
        forbidden = copy.deepcopy(valid)
        forbidden["tool_calls"][0]["input"]["subagent_type"] = "spec-context-analyst"
        variants.append(("forbidden", forbidden, "fail"))
        unknown = copy.deepcopy(valid)
        unknown["tool_calls"][0]["input"]["subagent_type"] = "other-analyst"
        variants.append(("unknown-role", unknown, "fail"))
        nested = copy.deepcopy(valid)
        nested["tool_calls"][0]["parent_id"] = "parent-agent"
        nested["native_metadata"]["subagent_return_order"]["returns"].pop(0)
        variants.append(("nested", nested, "fail"))
        failed = copy.deepcopy(valid)
        failed["tool_calls"][0]["success"] = False
        failed["native_metadata"]["subagent_return_order"]["returns"].pop(0)
        variants.append(("failed", failed, "fail"))
        for name, prompt in (
            ("missing-marker", "Inspect the item."),
            ("wrong-marker", "[[native-eval-item:other-item]]"),
            ("duplicate-marker", "[[native-eval-item:dispatch-i1]] [[native-eval-item:dispatch-i1]]"),
        ):
            changed = copy.deepcopy(valid)
            changed["tool_calls"][0]["input"]["prompt"] = prompt
            changed["native_metadata"]["native_subagent_dispatch_attribution"]["calls"][0].update(
                _opaque_message(prompt)
            )
            variants.append((name, changed, "fail"))
        missing_return = copy.deepcopy(valid)
        missing_return["native_metadata"]["subagent_return_order"]["returns"].pop()
        variants.append(("missing-return", missing_return, "invalid"))
        wrong_authority = copy.deepcopy(valid)
        wrong_authority["native_metadata"]["subagent_return_order"]["returns"][0][
            "authority"
        ] = "codex-parent-delivery"
        variants.append(("wrong-return-authority", wrong_authority, "invalid"))
        wrong_return_id = copy.deepcopy(valid)
        wrong_return_id["native_metadata"]["subagent_return_order"]["returns"][0][
            "call_id"
        ] = "other-call"
        variants.append(("wrong-return-call", wrong_return_id, "invalid"))
        forged = copy.deepcopy(valid)
        forged["native_metadata"]["native_subagent_dispatch_attribution"]["calls"][0][
            "message_sha256"
        ] = "0" * 64
        variants.append(("forged-attribution", forged, "invalid"))
        wrong_attribution_id = copy.deepcopy(valid)
        wrong_attribution_id["native_metadata"]["native_subagent_dispatch_attribution"][
            "calls"
        ][0]["call_id"] = "other-call"
        variants.append(("wrong-attribution-call", wrong_attribution_id, "invalid"))

        for name, evidence, expected in variants:
            with self.subTest(name=name):
                self.assertEqual(
                    grade_observation(value, evidence, host="claude")["status"], expected,
                )

    @staticmethod
    def _synthesis_case() -> dict[str, object]:
        return case([
            {
                "id": "mechanism", "requirement": "r1", "type": "native_synthesis_mechanism",
                "artifact_path": "scenario-output/consensus-result.json",
                "per_host": copy.deepcopy(NATIVE_SYNTHESIS_MECHANISMS),
            },
            {
                "id": "source-a", "requirement": "r1", "type": "file_access",
                "operation": "read_file", "path": "scenario-inputs/analyst-a.md",
            },
            {
                "id": "source-b", "requirement": "r1", "type": "file_access",
                "operation": "read_file", "path": "scenario-inputs/analyst-b.md",
            },
            {
                "id": "artifact", "requirement": "r1", "type": "json_field",
                "path": "scenario-output/consensus-result.json",
                "field_path": ["decision"], "expected": "escape_to_round_2",
            },
        ])

    @staticmethod
    def _synthesis_observation(host: str) -> dict[str, object]:
        is_claude = host == "claude"
        returned = ({"type": "text", "text": "low confidence; escape to round 2"}
                    if is_claude else "result")
        encoded = (json.dumps(returned, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":"), allow_nan=False).encode("utf-8")
                   if is_claude else b"result")
        digest = hashlib.sha256(encoded).hexdigest()
        read_name = "Read" if is_claude else "command_execution"
        read_key = "file_path" if is_claude else "command"
        reads = [
            {
                "id": f"read-{suffix}", "name": read_name,
                "input": {read_key: path if is_claude else f"cat {path}"},
                "output": f"option {suffix}", "success": True,
                "parent_id": None, "position": position,
            }
            for position, (suffix, path) in enumerate((
                ("a", "scenario-inputs/analyst-a.md"),
                ("b", "scenario-inputs/analyst-b.md"),
            ))
        ]
        role_input = ({"subagent_type": "speckit-pro:consensus-synthesizer"}
                      if is_claude else {"role": "consensus-synthesizer"})
        change = ({
            "id": "write", "name": "Write",
            "input": {"file_path": "scenario-output/consensus-result.json"},
            "output": {"changed": True}, "success": True, "parent_id": None, "position": 4,
        } if is_claude else {
            "id": "change", "name": "file_change",
            "input": {"changes": [{"path": "scenario-output/consensus-result.json"}]},
            "output": {"changed": True}, "success": True, "parent_id": None, "position": 4,
        })
        stream, turn = (("claude-main", None) if is_claude else ("root-thread", "root-turn"))
        native_metadata = {
            "subagent_return_order": {
                "schema": "native-subagent-return-order/v1", "scope": "direct-root-only",
                "returns": [{
                    "tool_call_index": 2, "call_id": "synth",
                    "authority": "claude-tool-result" if is_claude else "codex-parent-delivery",
                    "native_stream": stream, "native_turn": turn, "completion_index": 3,
                    "content_sha256": digest, "content_bytes": len(encoded),
                    "content_nonempty": True,
                }],
                "parent_file_changes": [{
                    "tool_call_index": 3, "call_id": change["id"],
                    "native_stream": stream, "native_turn": turn, "native_event_index": 4,
                    "paths": ["scenario-output/consensus-result.json"],
                }],
            },
        }
        if is_claude:
            native_metadata["claude_tool_results"] = [{
                "tool_call_index": 2, "id": "synth", "tool_result_position": 3,
                "output_sha256": digest, "output_bytes": len(encoded),
            }]
        else:
            native_metadata.update({
                "nested_rollout": {"dispatches": [{"id": "synth", "delivery": {
                    "native_event_index": 3, "turn_id": turn,
                    "sha256": digest, "bytes": len(encoded),
                }}]},
                "nested_merge": {"events": [{
                    "id": change["id"], "thread_id": stream, "turn_id": turn,
                    "native_event_index": 4,
                }]},
            })
        return observation(
            tool_calls=[*reads, {
                "id": "synth", "name": "subagent", "input": role_input,
                "output": returned, "success": True, "parent_id": None, "position": 2,
            }, change],
            artifacts={"scenario-output/consensus-result.json":
                       '{"decision":"escape_to_round_2"}'},
            native_metadata=native_metadata,
        )

    def test_rejects_missing_malformed_incomplete_and_error_evidence(self) -> None:
        value = case()
        for evidence in (
            {},
            observation(completed=False),
            observation(error="provider failed"),
            observation(completed="true"),
            observation(tool_calls=[{"name": "Read", "input": {}, "success": "true"}]),
            observation(artifacts={"../escape": "text"}),
            observation(unknown=True),
            observation(native_metadata={"model": object()}),
            observation(tool_calls=[{"name": "Read", "input": {}, "success": True, "output": object()}]),
        ):
            result = grade_observation(value, evidence)
            self.assertEqual(result["status"], "invalid", evidence)
            self.assertTrue(all(row["verdict"] == "invalid" for row in result["checks"]))

    def test_selection_rejects_noop_wrong_multiple_and_duplicate_false_positives(self) -> None:
        value = case()
        self.assertEqual(grade_observation(value, observation())["status"], "pass")
        self.assertEqual(grade_observation(value, observation(activations=[]))["status"], "fail")
        self.assertEqual(grade_observation(value, observation(activations=["wrong"]))["status"], "fail")
        self.assertEqual(grade_observation(value, observation(activations=["skill", "sibling"]))["status"], "fail")
        self.assertEqual(grade_observation(value, observation(activations=["skill", "skill"]))["status"], "fail")
        noop = case([{
            "id": "selection", "requirement": "r1", "type": "selection",
            "expected": [], "allowed_extra": [],
        }])
        self.assertEqual(grade_observation(noop, observation(activations=[]))["status"], "pass")
        self.assertEqual(grade_observation(noop, observation(activations=["skill"]))["status"], "fail")

    def test_text_file_and_json_checks_distinguish_failure_from_invalid_evidence(self) -> None:
        checks = [
            {"id": "text", "requirement": "r1", "type": "text", "source": "final_text", "pattern": r"done$"},
            {"id": "artifact-text", "requirement": "r1", "type": "text", "source": "report.txt", "pattern": "ready"},
            {"id": "exists", "requirement": "r1", "type": "file_exists", "path": "report.txt", "exists": True},
            {"id": "absent", "requirement": "r1", "type": "file_exists", "path": "forbidden.txt", "exists": False},
            {"id": "json", "requirement": "r1", "type": "json_field", "path": "result.json", "field_path": ["data", 0, "ok"], "expected": True},
        ]
        value = case(checks)
        artifacts = {"report.txt": "ready", "result.json": '{"data":[{"ok":true}]}'}
        self.assertEqual(grade_observation(value, observation(artifacts=artifacts))["status"], "pass")
        strict = copy.deepcopy(value)
        strict["checks"][-1]["expected"] = 1
        self.assertEqual(grade_observation(strict, observation(artifacts=artifacts))["status"], "fail")
        missing = grade_observation(value, observation(artifacts={"report.txt": "ready"}))
        self.assertEqual(missing["status"], "fail")
        missing_text = grade_observation(value, observation(artifacts={"result.json": artifacts["result.json"]}))
        self.assertEqual(missing_text["status"], "fail")
        self.assertEqual(next(row for row in missing_text["checks"] if row["id"] == "artifact-text")["verdict"], "fail")
        for content in ("NaN", "{", '{"data":[],"data":[{"ok":true}]}'):
            with self.subTest(content=content):
                malformed = grade_observation(value, observation(artifacts={"report.txt": "ready", "result.json": content}))
                self.assertEqual(malformed["status"], "fail")
        unavailable = grade_observation(value, observation(error="artifact capture failed", artifacts={}))
        self.assertEqual(unavailable["status"], "invalid")
        mismatch = grade_observation(value, observation(final_text="wrong", artifacts=artifacts))
        self.assertEqual(mismatch["status"], "fail")

    def test_tool_count_input_order_success_and_metadata(self) -> None:
        checks = [
            {"id": "used", "requirement": "r1", "type": "tool_used", "name": "Read", "min": 1, "max": 1, "input_regex": r'input\.txt'},
            {"id": "order", "requirement": "r1", "type": "tool_order", "before": "Read", "after": "Write"},
        ]
        value = case(checks)
        calls = [
            {"name": "Read", "input": {"path": "input.txt"}, "output": "fixture", "success": True, "id": "call-1", "parent_id": None, "position": 0},
            {"name": "Write", "input": {"path": "result.txt"}, "output": {"changed": True}, "success": True, "id": "call-2", "parent_id": "call-1", "position": 1},
        ]
        native = observation(tool_calls=calls, native_metadata={"model": "runtime-model", "tools": ["Read", "Write"]})
        self.assertEqual(grade_observation(value, native)["status"], "pass")
        reversed_calls = list(reversed(calls))
        self.assertEqual(grade_observation(value, observation(tool_calls=reversed_calls))["status"], "fail")
        failed_read = copy.deepcopy(calls)
        failed_read[0]["success"] = False
        self.assertEqual(grade_observation(value, observation(tool_calls=failed_read))["status"], "fail")
        extra_read = [calls[0], calls[0], calls[1]]
        self.assertEqual(grade_observation(value, observation(tool_calls=extra_read))["status"], "fail")
        bad_metadata = copy.deepcopy(calls)
        bad_metadata[0]["position"] = True
        self.assertEqual(grade_observation(value, observation(tool_calls=bad_metadata))["status"], "invalid")

    def test_tool_count_can_include_failed_attempts_without_changing_the_default(self) -> None:
        base = {
            "id": "forbidden", "requirement": "r1", "type": "tool_used",
            "name": "Write", "min": 0, "max": 0, "input_regex": r"forbidden\.txt",
        }
        calls = [
            {
                "name": "Write", "input": {"file_path": "allowed.txt"},
                "output": "ok", "success": True,
            },
            {
                "name": "Write", "input": {"file_path": "forbidden.txt"},
                "output": "denied", "success": False,
            },
        ]
        evidence = observation(tool_calls=calls)
        self.assertEqual(grade_observation(case([base]), evidence)["status"], "pass")
        explicit_default = copy.deepcopy(base)
        explicit_default["include_failed"] = False
        self.assertEqual(grade_observation(case([explicit_default]), evidence)["status"], "pass")
        attempted = copy.deepcopy(base)
        attempted["include_failed"] = True
        self.assertEqual(grade_observation(case([attempted]), evidence)["status"], "fail")

        successful_path = copy.deepcopy(base)
        successful_path["input_regex"] = r"allowed\.txt"
        self.assertEqual(grade_observation(case([successful_path]), evidence)["status"], "fail")
        absent_path = copy.deepcopy(attempted)
        absent_path["input_regex"] = r"missing\.txt"
        self.assertEqual(grade_observation(case([absent_path]), evidence)["status"], "pass")

        for malformed in ("true", 1, 0, None, [], {}):
            with self.subTest(malformed=malformed):
                direct = copy.deepcopy(base)
                direct["include_failed"] = malformed
                self.assertEqual(grade_observation(case([direct]), evidence)["status"], "invalid")
        malformed_observation = copy.deepcopy(calls)
        malformed_observation[1]["success"] = "false"
        self.assertEqual(
            grade_observation(case([attempted]), observation(tool_calls=malformed_observation))["status"],
            "invalid",
        )

    def test_file_access_uses_exact_successful_native_reads_not_tool_input_mentions(self) -> None:
        value = case([{
            "id": "read-plan", "requirement": "r1", "type": "file_access",
            "operation": "read_file", "path": "plan.md",
        }])
        claude_call = {
            "id": "read-1", "name": "Read",
            "input": {"file_path": "/private/tmp/native-eval/workspace/plan.md"},
            "output": "plan", "success": True, "position": 1, "parent_id": None,
        }
        claude = observation(
            tool_calls=[claude_call],
            native_metadata={"cwd": "/private/tmp/native-eval/workspace"},
        )
        self.assertEqual(grade_observation(value, claude)["status"], "pass")

        wrong_prefix = copy.deepcopy(claude)
        wrong_prefix["tool_calls"][0]["input"]["file_path"] = \
            "/private/tmp/native-eval/workspace/not-plan.md"
        self.assertEqual(grade_observation(value, wrong_prefix)["status"], "fail")

        relative = copy.deepcopy(claude)
        relative.pop("native_metadata")
        relative["tool_calls"][0]["input"]["file_path"] = "plan.md"
        self.assertEqual(grade_observation(value, relative)["status"], "pass")

        failed = copy.deepcopy(claude)
        failed["tool_calls"][0]["success"] = False
        self.assertEqual(grade_observation(value, failed)["status"], "fail")

        unsupported = observation(tool_calls=[{
            "name": "command_execution", "input": {"command": "echo plan.md"},
            "output": "plan.md", "success": True,
        }])
        self.assertEqual(grade_observation(value, unsupported)["status"], "fail")

        codex = observation(tool_calls=[{
            "name": "command_execution", "input": {"command": "cat plan.md"},
            "output": "plan", "success": True,
        }])
        self.assertEqual(grade_observation(value, codex)["status"], "pass")
        codex["tool_calls"][0]["input"]["command"] = "cat /tmp/plan.md"
        self.assertEqual(grade_observation(value, codex)["status"], "fail")

    def test_semantic_checks_need_exact_typed_evidence_backed_verdicts(self) -> None:
        value = case([{
            "id": "judge", "requirement": "r1", "type": "semantic",
            "rubric": "The response gives an actionable and accurate explanation.",
        }])
        self.assertEqual(grade_observation(value, observation())["status"], "needs_judge")
        passed = {"judge": {"passed": True, "evidence": ["artifact:judge/judge.json"]}}
        self.assertEqual(grade_observation(value, observation(), passed)["status"], "pass")
        failed = {"judge": {"passed": False, "evidence": ["artifact:judge/judge.json"]}}
        self.assertEqual(grade_observation(value, observation(), failed)["status"], "fail")
        malformed = (
            {},
            {"judge": {"passed": "true", "evidence": ["artifact:judge/judge.json"]}},
            {"judge": {"passed": True, "evidence": []}},
            {"judge": {"passed": True, "evidence": ["artifact:judge/judge.json"]}, "extra": {"passed": True, "evidence": ["x"]}},
        )
        for verdicts in malformed:
            self.assertEqual(grade_observation(value, observation(), verdicts)["status"], "invalid")

    def test_cross_host_equality_cannot_override_failed_requirements(self) -> None:
        value = case([
            {
                "id": "selection", "requirement": "r1", "type": "selection",
                "expected": ["skill"], "allowed_extra": [],
            },
            {
                "id": "text", "requirement": "r1", "type": "text",
                "source": "final_text", "pattern": "required result",
            },
        ])
        wrong = observation(final_text="same wrong output")
        claude = grade_observation(value, wrong)
        codex = grade_observation(value, copy.deepcopy(wrong))
        self.assertEqual(claude, codex)
        self.assertEqual(claude["status"], "fail")
        self.assertEqual(codex["status"], "fail")
        self.assertEqual([row["verdict"] for row in claude["checks"]], ["pass", "fail"])
        self.assertEqual([row["verdict"] for row in codex["checks"]], ["pass", "fail"])

    def test_native_synthesis_mechanism_uses_only_the_trusted_host_policy(self) -> None:
        value = self._synthesis_case()
        claude = self._synthesis_observation("claude")
        codex = self._synthesis_observation("codex")
        self.assertEqual(grade_observation(value, claude, host="claude")["status"], "pass")
        self.assertEqual(grade_observation(value, codex, host="codex")["status"], "pass")
        self.assertEqual(grade_observation(value, claude)["status"], "invalid")
        self.assertEqual(grade_observation(value, claude, host="other")["status"], "invalid")
        spoofed = copy.deepcopy(claude)
        spoofed["native_metadata"]["host"] = "codex"
        self.assertEqual(grade_observation(value, spoofed, host="claude")["status"], "pass")
        self.assertEqual(grade_observation(value, spoofed, host="codex")["status"], "fail")

        legacy = case()
        self.assertEqual(grade_observation(legacy, observation(), host="other")["status"], "pass")

    def test_each_host_synthesis_requires_completed_exact_role_then_parent_write(self) -> None:
        value = self._synthesis_case()
        valid = self._synthesis_observation("claude")
        variants = []

        wrong_role = copy.deepcopy(valid)
        wrong_role["tool_calls"][2]["input"]["subagent_type"] = "speckit-pro:codebase-analyst"
        variants.append((wrong_role, "fail"))
        nested = copy.deepcopy(valid)
        nested["tool_calls"][2]["parent_id"] = "parent-agent"
        variants.append((nested, "invalid"))
        duplicated = copy.deepcopy(valid)
        duplicate_call = copy.deepcopy(duplicated["tool_calls"][2])
        duplicate_call["id"] = "synth-again"
        duplicated["tool_calls"].append(duplicate_call)
        variants.append((duplicated, "invalid"))
        failed = copy.deepcopy(valid)
        failed["tool_calls"][2]["success"] = False
        variants.append((failed, "fail"))
        missing_receipt = copy.deepcopy(valid)
        del missing_receipt["native_metadata"]["subagent_return_order"]
        variants.append((missing_receipt, "invalid"))
        empty = copy.deepcopy(valid)
        empty["tool_calls"][2]["output"] = {"type": "text", "text": " "}
        variants.append((empty, "invalid"))
        early_write = copy.deepcopy(valid)
        early_write["tool_calls"][3]["position"] = 2
        early_write["native_metadata"]["subagent_return_order"]["parent_file_changes"][0]["native_event_index"] = 2
        variants.append((early_write, "fail"))
        wrong_turn = copy.deepcopy(valid)
        wrong_turn["native_metadata"]["subagent_return_order"]["returns"][0]["native_turn"] = "other-turn"
        variants.append((wrong_turn, "invalid"))
        wrong_writer = copy.deepcopy(valid)
        wrong_writer["tool_calls"][3]["parent_id"] = "synth"
        variants.append((wrong_writer, "invalid"))
        wrong_path = copy.deepcopy(valid)
        wrong_path["tool_calls"][3]["input"]["file_path"] = "scenario-output/other.json"
        variants.append((wrong_path, "invalid"))

        for evidence, expected in variants:
            with self.subTest(expected=expected, evidence=evidence):
                self.assertEqual(grade_observation(value, evidence, host="claude")["status"], expected)

        value = self._synthesis_case()
        valid = self._synthesis_observation("codex")
        variants = []

        missing = copy.deepcopy(valid)
        missing["tool_calls"].pop(2)
        variants.append((missing, "fail"))
        wrong_role = copy.deepcopy(valid)
        wrong_role["tool_calls"][2]["input"]["role"] = "codebase-analyst"
        variants.append((wrong_role, "fail"))
        nested = copy.deepcopy(valid)
        nested["tool_calls"][2]["parent_id"] = "other-agent"
        variants.append((nested, "invalid"))
        failed = copy.deepcopy(valid)
        failed["tool_calls"][2]["success"] = False
        variants.append((failed, "fail"))
        no_receipt = copy.deepcopy(valid)
        del no_receipt["native_metadata"]["subagent_return_order"]
        variants.append((no_receipt, "invalid"))
        shell_write = copy.deepcopy(valid)
        shell_write["tool_calls"][3] = {
            "id": "shell", "name": "command_execution",
            "input": {"command": "printf result > scenario-output/consensus-result.json"},
            "output": "", "success": True, "parent_id": None, "position": 4,
        }
        variants.append((shell_write, "invalid"))
        response_only = copy.deepcopy(valid)
        response_only["tool_calls"].pop(3)
        response_only["final_text"] = "I wrote the result."
        variants.append((response_only, "invalid"))
        child_writer = copy.deepcopy(valid)
        child_writer["tool_calls"][3]["parent_id"] = "synth"
        variants.append((child_writer, "invalid"))
        late_read = copy.deepcopy(valid)
        late_read["tool_calls"] = [late_read["tool_calls"][2], *late_read["tool_calls"][:2],
                                   late_read["tool_calls"][3]]
        variants.append((late_read, "fail"))
        missing_read = copy.deepcopy(valid)
        missing_read["tool_calls"].pop(1)
        variants.append((missing_read, "fail"))
        wrong_authority = copy.deepcopy(valid)
        wrong_authority["native_metadata"]["subagent_return_order"]["returns"][0][
            "authority"
        ] = "claude-tool-result"
        variants.append((wrong_authority, "invalid"))

        for evidence, expected in variants:
            with self.subTest(expected=expected, evidence=evidence):
                self.assertEqual(grade_observation(value, evidence, host="codex")["status"], expected)

    def test_synthesis_mechanism_does_not_override_wrong_artifact_content(self) -> None:
        value = self._synthesis_case()
        evidence = self._synthesis_observation("codex")
        evidence["artifacts"]["scenario-output/consensus-result.json"] = '{"decision":"human_review"}'
        result = grade_observation(value, evidence, host="codex")
        self.assertEqual(result["status"], "fail")
        self.assertEqual(next(row for row in result["checks"] if row["id"] == "mechanism")["verdict"], "pass")
        self.assertEqual(next(row for row in result["checks"] if row["id"] == "artifact")["verdict"], "fail")

class NativeFixtureMaterializerTests(unittest.TestCase):
    def _plan(self, root: Path, *, same_tree: bool = False) -> dict[str, object]:
        source = root / "source"
        source.mkdir(parents=True)
        (source / "baseline.txt").write_text("baseline\n", encoding="utf-8")
        (source / "feature.txt").write_text("baseline\n" if same_tree else "feature\n", encoding="utf-8")
        digest = lambda name: __import__("hashlib").sha256((source / name).read_bytes()).hexdigest()
        return {
            "schema_version": "native-eval-fixtures/v2",
            "source_root": str(source),
            "fixtures": [{"source": "feature.txt", "destination": "README.md", "sha256": digest("feature.txt")}],
            "git_repository": {
                "recipe": "baseline-feature-origin-main/v1",
                "baseline": [{"source": "baseline.txt", "destination": "README.md", "sha256": digest("baseline.txt")}],
            },
        }

    def test_v1_population_stays_a_plain_confined_copy(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source, workspace = root / "source", root / "workspace"
            source.mkdir()
            workspace.mkdir()
            payload = b"plain\n"
            (source / "plain.txt").write_bytes(payload)
            plan = {"schema_version": "native-eval-fixtures/v1", "source_root": str(source), "fixtures": [{
                "source": "plain.txt", "destination": "plain.txt", "sha256": __import__("hashlib").sha256(payload).hexdigest(),
            }]}
            self.assertEqual(populate_workspace(plan, workspace), ["plain.txt"])
            self.assertEqual((workspace / "plain.txt").read_bytes(), payload)
            self.assertFalse((workspace / ".git").exists())

    def test_fixture_parent_symlink_escape_is_rejected_before_reading(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source, outside, workspace = root / "source", root / "outside", root / "workspace"
            source.mkdir()
            outside.mkdir()
            workspace.mkdir()
            (outside / "secret.txt").write_text("outside\n", encoding="utf-8")
            try:
                os.symlink(outside, source / "escape")
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            plan = {"schema_version": "native-eval-fixtures/v1", "source_root": str(source), "fixtures": [{
                "source": "escape/secret.txt", "destination": "secret.txt", "sha256": "0" * 64,
            }]}
            with mock.patch.object(Path, "read_bytes", side_effect=AssertionError("outside file was read")):
                with self.assertRaisesRegex(ValueError, "escaped its staged root"):
                    populate_workspace(plan, workspace)
            self.assertEqual(list(workspace.iterdir()), [])

    def test_fixed_git_recipe_ignores_inherited_git_redirects_and_binds_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            workspace = root / "workspace"
            workspace.mkdir()
            hostile = root / "hostile-index"
            marker = root / "hostile-hook-ran"
            template = root / "hostile-template"
            hooks = template / "hooks"
            hooks.mkdir(parents=True)
            hook = hooks / "pre-commit"
            hook.write_text(f"#!/bin/sh\ntouch {marker}\n", encoding="utf-8")
            hook.chmod(0o700)
            global_config = root / "hostile-gitconfig"
            global_config.write_text(f"[core]\n\thooksPath = {hooks}\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {
                "GIT_DIR": str(root / "elsewhere"), "GIT_WORK_TREE": str(root / "elsewhere-worktree"),
                "GIT_INDEX_FILE": str(hostile), "GIT_OBJECT_DIRECTORY": str(root / "objects"),
                "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(root / "alternate"),
                "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.hooksPath", "GIT_CONFIG_VALUE_0": str(root),
                "GIT_CONFIG_GLOBAL": str(global_config), "GIT_TEMPLATE_DIR": str(template),
            }, clear=False):
                result = materialize_workspace(self._plan(root), workspace)
            receipt = result["git_repository"]
            self.assertEqual(receipt["recipe"], "baseline-feature-origin-main/v1")
            self.assertEqual(receipt["origin_main"], receipt["baseline_commit"])
            self.assertEqual(receipt["head"], receipt["feature_commit"])
            self.assertNotEqual(receipt["head"], receipt["origin_main"])
            self.assertEqual(receipt["branch"], "feature")
            self.assertTrue(receipt["clean"] and receipt["nonempty_diff"])
            self.assertEqual((workspace / "README.md").read_text(encoding="utf-8"), "feature\n")
            self.assertFalse(hostile.exists())
            self.assertFalse(marker.exists())

    def test_fixed_git_recipe_rejects_empty_semantic_diff(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            workspace = root / "workspace"
            workspace.mkdir()
            with self.assertRaisesRegex(ValueError, "nonempty semantic diff"):
                materialize_workspace(self._plan(root, same_tree=True), workspace)

    def test_v1_entrypoint_rejects_v2_before_any_workspace_effect(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            workspace = root / "workspace"
            workspace.mkdir()
            with self.assertRaisesRegex(ValueError, "only accepts v1"):
                populate_workspace(self._plan(root), workspace)
            self.assertEqual(list(workspace.iterdir()), [])

    def test_git_recipe_rejects_casefolded_control_paths_before_writes(self) -> None:
        for target, baseline in ((".GiT/config", True), (".aGeNtS/config", True), (".CoDeX/config", False),
                                 (".cLaUdE/config", False), (".gIt/config", False)):
            with self.subTest(target=target, baseline=baseline), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                workspace = root / "workspace"
                workspace.mkdir()
                plan = self._plan(root)
                records = plan["git_repository"]["baseline"] if baseline else plan["fixtures"]
                records[0]["destination"] = target
                with self.assertRaisesRegex(ValueError, "reserved runtime path"):
                    materialize_workspace(plan, workspace)
                self.assertEqual(list(workspace.iterdir()), [])

    def test_git_recipe_rejects_dirty_target_and_has_relocatable_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            dirty = root / "dirty"
            dirty.mkdir()
            (dirty / "keep.txt").write_text("keep\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "workspace must be empty"):
                materialize_workspace(self._plan(root / "dirty-plan"), dirty)
            self.assertEqual((dirty / "keep.txt").read_text(encoding="utf-8"), "keep\n")
            left, right = root / "left", root / "right"
            left.mkdir()
            right.mkdir()
            left_receipt = materialize_workspace(self._plan(root / "left-plan"), left)["git_repository"]
            right_receipt = materialize_workspace(self._plan(root / "right-plan"), right)["git_repository"]
            self.assertEqual(left_receipt, right_receipt)

    def test_git_inspection_binds_controls_before_any_repository_git_command(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            workspace = root / "workspace"
            workspace.mkdir()
            expected = materialize_workspace(self._plan(root), workspace)["git_repository"]
            exclude = workspace / ".git" / "info" / "exclude"
            exclude.parent.mkdir()
            exclude.write_text("# controller-owned exclusion\n", encoding="utf-8")
            controls = fixture_setup.snapshot_git_repository_controls(workspace)
            self.assertEqual(fixture_setup.inspect_git_repository(workspace, controls), expected)
            config = workspace / ".git" / "config"
            config.write_text("[core]\n\thooksPath = /unsafe\n", encoding="utf-8")
            with mock.patch("native_eval_fixture_setup._run_git", side_effect=AssertionError("git was invoked")):
                with self.assertRaisesRegex(ValueError, "controls do not match"):
                    fixture_setup.inspect_git_repository(workspace, controls)

    def test_git_inspection_rejects_redirects_and_symlinks_before_git(self) -> None:
        for path in ("commondir", "objects/info/alternates", "HEAD"):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                workspace = root / "workspace"
                workspace.mkdir()
                materialize_workspace(self._plan(root), workspace)
                exclude = workspace / ".git" / "info" / "exclude"
                exclude.parent.mkdir()
                exclude.write_text("# controller-owned exclusion\n", encoding="utf-8")
                controls = fixture_setup.snapshot_git_repository_controls(workspace)
                target = workspace / ".git" / path
                if path == "HEAD":
                    target.rename(target.with_suffix(".saved"))
                    os.symlink(target.with_suffix(".saved"), target)
                else:
                    target.write_text("redirect\n", encoding="utf-8")
                with mock.patch("native_eval_fixture_setup._run_git", side_effect=AssertionError("git was invoked")):
                    with self.assertRaisesRegex(ValueError, "control paths contain (a symlink|a redirect)"):
                        fixture_setup.inspect_git_repository(workspace, controls)

    def test_v2_cli_writes_one_external_actual_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            workspace, receipt_path, plan_path = root / "workspace", root / "receipt.json", root / "plan.json"
            workspace.mkdir()
            plan = self._plan(root)
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            output = io.StringIO()
            with mock.patch("native_eval_fixture_setup.Path.cwd", return_value=workspace), redirect_stdout(output):
                self.assertEqual(fixture_setup.main(["--receipt-path", str(receipt_path), str(plan_path)]), 0)
            actual = json.loads(output.getvalue())
            self.assertEqual(json.loads(receipt_path.read_text(encoding="utf-8")), actual)
            self.assertEqual(stat.S_IMODE(receipt_path.stat().st_mode), 0o600)
            self.assertIn("git_repository", actual)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            workspace, receipt_path, plan_path = root / "workspace", root / "receipt.json", root / "plan.json"
            workspace.mkdir()
            receipt_path.write_text("old", encoding="utf-8")
            plan_path.write_text(json.dumps(self._plan(root)), encoding="utf-8")
            with mock.patch("native_eval_fixture_setup.Path.cwd", return_value=workspace):
                with self.assertRaisesRegex(ValueError, "receipt path already exists"):
                    fixture_setup.main(["--receipt-path", str(receipt_path), str(plan_path)])
            self.assertEqual(list(workspace.iterdir()), [])

    def test_git_command_failures_and_receipt_mismatch_fail_closed(self) -> None:
        completed_failure = subprocess.CompletedProcess(["git"], 1, b"", b"failure")
        with mock.patch("native_eval_fixture_setup.subprocess.run", return_value=completed_failure):
            for label in ("init", "commit baseline", "set origin/main"):
                with self.subTest(label=label), self.assertRaisesRegex(ValueError, f"{label} failed"):
                    fixture_setup._run_git("git", Path.cwd(), {}, ["status"], label)
        with mock.patch("native_eval_fixture_setup.subprocess.run", side_effect=subprocess.TimeoutExpired("git", 30)):
            with self.assertRaisesRegex(ValueError, "init timed out"):
                fixture_setup._run_git("git", Path.cwd(), {}, ["init"], "init")
        state = {"git": "git", "environment": {}, "hooks": Path.cwd(), "baseline_commit": "baseline", "baseline_tree": "base-tree"}
        with mock.patch("native_eval_fixture_setup._run_git", return_value=""), \
             mock.patch("native_eval_fixture_setup.subprocess.run", side_effect=subprocess.TimeoutExpired("git", 30)):
            with self.assertRaisesRegex(ValueError, "semantic diff check timed out"):
                fixture_setup._finish_git_repository(Path.cwd(), state)
        outputs = iter(("", "", "wrong-ref", "base-tree", "head", "tree", "baseline", "feature", ""))
        with mock.patch("native_eval_fixture_setup._run_git", side_effect=lambda *_args: next(outputs)), \
             mock.patch("native_eval_fixture_setup.subprocess.run", return_value=subprocess.CompletedProcess(["git"], 1, b"", b"")):
            with self.assertRaisesRegex(ValueError, "receipt invariants"):
                fixture_setup._finish_git_repository(Path.cwd(), state)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            workspace = root / "workspace"
            workspace.mkdir()
            with mock.patch("native_eval_fixture_setup.shutil.which", return_value=None):
                with self.assertRaisesRegex(ValueError, "executable is unavailable"):
                    materialize_workspace(self._plan(root), workspace)
            self.assertEqual(list(workspace.iterdir()), [])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(NativeEvalCatalogTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(NativeEvalGradingTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(NativeFixtureMaterializerTests))
    raise SystemExit(run_counted(suite, label="test-native-eval-contracts"))
