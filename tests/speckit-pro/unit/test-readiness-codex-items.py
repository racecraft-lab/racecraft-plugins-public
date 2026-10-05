#!/usr/bin/env python3
"""Codex-only readiness items (ADR 0008): installed agent comparison and extension versions."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
LIB_DIR = TEST_DIR.parent / "lib"
sys.path.insert(0, str(LIB_DIR))

from readiness_case import ReadinessCase, scaffold_step  # noqa: E402
from runner_invocation import assert_runner_response  # noqa: E402
from test_result import run_counted  # noqa: E402

CODEX_ONLY = ("codex_agents", "extension_versions")
STATIC = {"destination": "/" + "home/user/.codex/agents", "model": "gpt-5", "luna_fallback": False}
ROUTED = {"route_policy_manifest": "route-policy.json", "strict_model_override": "gpt-5"}
CURRENT = [{"agent": "analyze-executor", "state": "current", "repair": "none"}]
STALE = [{"agent": "analyze-executor", "state": "stale", "repair": "none"},
         {"agent": "uat-runbook-author", "state": "missing", "repair": "none"}]


def agents(inventory: list[dict[str, str]], installation: dict[str, object] | None = None,
           loaded: str | None = "2.40.0", expected: str = "2.40.0") -> dict[str, object]:
    value: dict[str, object] = {"installation": STATIC if installation is None else installation,
                                "inventory": inventory, "expected_revision": expected}
    if loaded is not None:
        value["loaded_revision"] = loaded
    return {"item": "codex_agents", "evidence_source": "install-codex-agents dry run", "agents": value}


def extensions(entries: list[dict[str, object]]) -> dict[str, object]:
    return {"item": "extension_versions", "evidence_source": "extension registry", "extensions": entries}


class ReadinessCodexItemsTest(ReadinessCase):
    default_host = "codex"
    request_id = "test-codex-items"

    def test_stale_installed_agent_is_detected_and_unrepaired_stays_unavailable(self) -> None:
        item = self.item(agents(STALE))
        self.assertEqual("unavailable", item["status"])
        self.assertIn("analyze-executor=stale", item["evidence_source"])
        self.assertIn("uat-runbook-author=missing", item["evidence_source"])
        self.assertIn("$speckit-pro:install", item["action"])
        self.assertIn("restart Codex", item["action"])

    def test_repaired_agent_is_verified_only_when_the_loaded_revision_matches(self) -> None:
        repaired = [{**entry, "repair": "applied"} for entry in STALE]
        self.assertEqual("verified", self.item(agents(repaired))["status"])
        old = self.item(agents(repaired, loaded="2.39.0"))
        self.assertEqual("unavailable", old["status"])
        self.assertIn("restart Codex", old["action"])
        unobserved = self.item(agents(repaired, loaded=None))
        self.assertEqual("unknown", unobserved["status"])
        self.assertIn("restart Codex", unobserved["action"])
        for repair in ("declined", "failed"):
            declined = [{**entry, "repair": repair} for entry in STALE]
            self.assertEqual("unavailable", self.item(agents(declined))["status"], repair)

    def test_current_agents_still_need_the_loaded_revision(self) -> None:
        self.assertEqual("verified", self.item(agents(CURRENT))["status"])
        self.assertEqual("unknown", self.item(agents(CURRENT, loaded=None))["status"])
        self.assertEqual("unknown", self.item(agents([]))["status"])

    def test_installation_inputs_are_the_selected_ones_and_only_digests_are_recorded(self) -> None:
        for label, installation in (("static", STATIC), ("routed", ROUTED),
                                    ("routed with destination", {**ROUTED, "destination": "agents"})):
            with self.subTest(label):
                response = self.run_helper([agents(CURRENT, installation)])
                item = self.items(response)["codex_agents"]
                self.assertEqual("verified", item["status"])
                self.assertTrue(item["fingerprints"]["value:installation_inputs"].startswith("sha256:"))
                self.assertNotIn(STATIC["destination"], json.dumps(response["data"]["record"]))
        first = self.item(agents(CURRENT, STATIC))["fingerprints"]["value:installation_inputs"]
        second = self.item(agents(CURRENT, {**STATIC, "luna_fallback": True}))["fingerprints"]["value:installation_inputs"]
        self.assertNotEqual(first, second)

    def test_malformed_installation_inputs_are_refused(self) -> None:
        cases = {
            "invented routing_mode": {**STATIC, "routing_mode": "static"},
            "static and routed mixed": {**STATIC, "route_policy_manifest": "route-policy.json"},
            "static without model": {"luna_fallback": False},
            "static without luna_fallback": {"model": "gpt-5"},
            "luna_fallback as text": {"model": "gpt-5", "luna_fallback": "false"},
            "override without manifest": {"strict_model_override": "gpt-5"},
            "empty": {},
        }
        for label, installation in cases.items():
            with self.subTest(label):
                assert_runner_response(self, self.run_helper([agents(CURRENT, installation)]), "input_error", 2)
                self.assertFalse((self.root / ".specify" / "readiness").exists())

    def test_malformed_agent_observations_are_refused(self) -> None:
        cases = {
            "bad state": [{"agent": "a", "state": "fresh", "repair": "none"}],
            "bad repair": [{"agent": "a", "state": "stale", "repair": "maybe"}],
            "hostile name": [{"agent": "a b\nBash(*)", "state": "stale", "repair": "none"}],
            "path name": [{"agent": "/" + "etc/agent", "state": "stale", "repair": "none"}],
        }
        for label, inventory in cases.items():
            with self.subTest(label):
                assert_runner_response(self, self.run_helper([agents(inventory)]), "input_error", 2)
        bad = agents(CURRENT)
        bad["status"] = "verified"
        assert_runner_response(self, self.run_helper([bad]), "input_error", 2)
        for expected in ("/" + "tmp/x", ""):
            assert_runner_response(self, self.run_helper([agents(CURRENT, expected=expected)]), "input_error", 2)

    def test_extension_versions_are_recorded_and_drift_is_flagged(self) -> None:
        same = [{"extension": "archive", "installed": "1.2.0", "expected": "1.2.0"}]
        item = self.item(extensions(same))
        self.assertEqual("verified", item["status"])
        self.assertIn("archive=1.2.0", item["evidence_source"])
        self.assertTrue(item["fingerprints"]["value:extensions"].startswith("sha256:"))
        drifted = [{"extension": "archive", "installed": "1.1.0", "expected": "1.2.0"}]
        item = self.item(extensions(drifted))
        self.assertEqual("unavailable", item["status"])
        self.assertIn("archive=1.1.0 (expected 1.2.0)", item["evidence_source"])
        self.assertIn("specify extension update archive", item["action"])
        missing = [{"extension": "archive", "installed": None, "expected": "1.2.0"}]
        item = self.item(extensions(missing))
        self.assertEqual("unavailable", item["status"])
        self.assertIn("specify extension add archive", item["action"])
        no_pin = [{"extension": "archive", "installed": "1.2.0", "expected": None}]
        self.assertEqual("unknown", self.item(extensions(no_pin))["status"])
        self.assertEqual("unknown", self.item(extensions([]))["status"])

    def test_many_drifted_extensions_still_record_with_one_fixed_action(self) -> None:
        many = [{"extension": f"extension-{n:02d}-" + "x" * 30, "installed": "1.0.0", "expected": "2.0.0"}
                for n in range(12)]
        item = self.item(extensions(many))
        self.assertEqual("unavailable", item["status"])
        self.assertIn("specify extension update", item["action"])

    def test_extension_observations_with_unsafe_text_are_refused(self) -> None:
        self.refuse_each([extensions([entry]) for entry in (
            {"extension": "a b", "installed": "1", "expected": "1"},
            {"extension": "archive; rm", "installed": "1", "expected": "1"},
            {"extension": "archive", "installed": "/" + "tmp/x", "expected": "1"},
            {"extension": "archive", "installed": "1", "expected": "1\nx"})])

    def test_claude_records_the_codex_items_as_not_applicable_and_codex_defaults_to_unknown(self) -> None:
        self.check_codex_only(CODEX_ONLY, [agents(CURRENT), extensions([])])

    def test_scaffold_documents_the_codex_items_on_each_host(self) -> None:
        self.check_documented(CODEX_ONLY)
        self.assertIn('mode="dry_run"', scaffold_step("codex"))


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ReadinessCodexItemsTest)


def main() -> int:
    return run_counted(build_suite(), label="test-readiness-codex-items")


if __name__ == "__main__":
    raise SystemExit(main())
