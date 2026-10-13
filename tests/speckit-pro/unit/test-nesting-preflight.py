#!/usr/bin/env python3
"""Nesting preflight: an observed nested spawn picks the plan-stage mode; depth settings never do (ADR 0026)."""

from __future__ import annotations

import importlib.util
import itertools
import json
import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
sys.path.insert(0, str(TEST_DIR.parent / "lib"))
sys.path.insert(0, str(REPO_ROOT / "speckit-pro"))

from host_skill_views import host_skill_root  # noqa: E402
from runner_invocation import run_runner  # noqa: E402
from test_result import run_counted  # noqa: E402

from speckit_pro_runner.helpers import nesting_preflight  # noqa: E402

VALIDATOR = REPO_ROOT / "tests/speckit-pro/layer6-integration/validate-canary-receipt.py"
SCHEMA = json.loads(VALIDATOR.with_name("canary-receipt.schema.json").read_text(encoding="utf-8"))


def resolve(**inputs: object) -> dict:
    """Call the helper through the runner, as the autopilot does; every call must succeed."""
    request = {"schema_version": "1.0", "request_id": "nesting-test", "helper_id": "resolve-nesting-mode",
               "operation": "resolve-nesting-mode", "mode": "read_only", "inputs": inputs}
    completed, response, _ = run_runner(request)
    assert completed.returncode == 0, (completed.returncode, response)
    assert response["status"] == "ok", response
    return response["data"]


class ModeDecisionTests(unittest.TestCase):
    def test_the_observed_spawn_picks_the_mode_on_each_host(self) -> None:
        expected = {"allowed": ("nested", "nested_spawn_allowed", False), "refused": ("flat", "nested_spawn_refused", True)}
        for host, (outcome, (mode, reason, has_prerequisite)) in itertools.product(("claude-code", "codex"), expected.items()):
            with self.subTest(host=host, outcome=outcome):
                data = resolve(host=host, nested_spawn=outcome)
                self.assertEqual((mode, reason, has_prerequisite), (data["mode"], data["reason"], bool(data["prerequisite"])))

    def test_a_configured_depth_alone_decides_neither_mode(self) -> None:
        for host, depth in (("claude-code", 3), ("claude-code", 1), ("codex", 2), ("codex", 0)):
            with self.subTest(host=host, depth=depth):
                self.assertEqual("flat", resolve(host=host, nested_spawn="refused", configured_depth=depth)["mode"])
                self.assertEqual("nested", resolve(host=host, nested_spawn="allowed", configured_depth=depth)["mode"])
                self.assertEqual("flat", resolve(host=host, configured_depth=depth)["mode"])

    def test_the_configured_depth_is_recorded_not_decided_on(self) -> None:
        self.assertEqual(3, resolve(host="codex", nested_spawn="refused", configured_depth=3)["configured_depth"])
        self.assertIsNone(resolve(host="codex", nested_spawn="refused")["configured_depth"])

    def test_prerequisites_name_the_setting_each_host_honors(self) -> None:
        claude = resolve(host="claude-code", nested_spawn="refused")["prerequisite"]
        self.assertIn("CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH", claude)
        codex = resolve(host="codex", nested_spawn="refused")["prerequisite"]
        self.assertIn("agents.max_depth", codex)
        self.assertIn("ignored", codex)


class DepthNeverStopsTheRunTests(unittest.TestCase):
    """Every input, however wrong, returns status ok with flat mode; an error would route into recovery."""

    def test_missing_garbled_and_unknown_evidence_degrades_to_flat(self) -> None:
        cases = [
            {}, {"host": "claude-code"}, {"host": "codex", "nested_spawn": "not_run"},
            {"host": "codex", "nested_spawn": "maybe"}, {"host": "codex", "nested_spawn": True},
            {"host": "codex", "nested_spawn": ["allowed"]}, {"host": "gemini", "nested_spawn": "allowed"},
            {"host": "codex", "nested_spawn": "allowed", "configured_depth": "deep"},
            {"host": "codex", "nested_spawn": "allowed", "configured_depth": -4},
            {"host": "codex", "nested_spawn": "allowed", "configured_depth": True},
            {"host": "codex", "nested_spawn": "allowed", "unexpected": 1},
        ]
        for inputs in cases:
            with self.subTest(inputs=inputs):
                data = resolve(**inputs)
                self.assertEqual("flat", data["mode"])
                self.assertIn(data["reason"], {"probe_not_run", "probe_invalid"})

    def test_insufficient_depth_is_never_a_stop(self) -> None:
        data = resolve(host="claude-code", nested_spawn="refused", configured_depth=1)
        self.assertEqual("flat", data["mode"])

    def test_no_stop_policy_label_keys_on_depth(self) -> None:
        for path in (REPO_ROOT / "speckit-pro/speckit_pro_runner/stop_policy.py",
                     REPO_ROOT / "speckit-pro/skills/speckit-autopilot/references/stop-policy.md"):
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("nesting", text, path.name)
            self.assertNotIn("spawn_depth", text, path.name)


class ReceiptModeTests(unittest.TestCase):
    """One source: the runner's mode values are exactly the canary receipt schema's `mode` enum."""

    def test_runner_modes_equal_the_receipt_schema_enum(self) -> None:
        self.assertEqual(set(SCHEMA["properties"]["mode"]["enum"]), set(nesting_preflight.MODES))

    def test_a_flat_result_records_mode_flat_in_a_receipt(self) -> None:
        spec = importlib.util.spec_from_file_location("canary_receipt", VALIDATOR)
        validator = importlib.util.module_from_spec(spec)
        sys.modules["canary_receipt"] = validator
        spec.loader.exec_module(validator)
        for nested_spawn, expected in (("refused", "flat"), ("allowed", "nested"), ("not_run", "flat")):
            with self.subTest(nested_spawn=nested_spawn):
                data = resolve(host="codex", nested_spawn=nested_spawn)
                self.assertEqual(expected, data["mode"])
                failures = validator.json_schema_failures(
                    data["mode"], SCHEMA["properties"]["mode"], SCHEMA, "receipt.mode")
                self.assertEqual([], failures)


class SkillContractTests(unittest.TestCase):
    def test_both_hosts_run_the_preflight_before_the_main_loop_and_dispatch_flat_otherwise(self) -> None:
        for host in ("claude", "codex"):
            text = (host_skill_root(host) / "speckit-autopilot" / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(host=host):
                self.assertIn("helper_id=resolve-nesting-mode", text)
                prerequisites = (host_skill_root(host) / "speckit-autopilot" / "references" / "prerequisites.md").read_text(encoding="utf-8")
                self.assertIn("resolve-nesting-mode", prerequisites)
                self.assertLess(text.index("## Step 1.5: Nesting Preflight"), text.index("## Step 2: Main Execution Loop"))
                self.assertIn("`data.prerequisite` once", text)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-nesting-preflight"))
