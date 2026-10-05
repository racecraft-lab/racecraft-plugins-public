#!/usr/bin/env python3
"""Codex approval, trust and sandbox readiness items (ADR 0008): facts about the session, never consent."""

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

TRUST_ITEMS = ("codex_approval_posture", "codex_hook_trust", "codex_local_access")
HASH = "a" * 64
OTHER_HASH = "b" * 64
POSTURE = {"approval_policy": "on-request", "sandbox_mode": "workspace-write", "approvals_reviewer": "user",
           "mcp_approval_mode": "prompt", "mcp_consent": "granted", "mcp_startup_timeout_sec": 10,
           "mcp_tool_timeout_sec": 60, "external_delegation": "allowed"}
ACCESS = {"loopback": "allowed", "temp_dir": "healthy", "egress_policy_ref": "egress-policy",
          "egress_policy_digest": HASH}


def posture(**changes: object) -> dict[str, object]:
    return {"item": "codex_approval_posture", "evidence_source": "codex session settings",
            "posture": {**POSTURE, **changes}}


def hook_trust(*entries: dict[str, object]) -> dict[str, object]:
    return {"item": "codex_hook_trust", "evidence_source": "/hooks review", "hooks": list(entries)}


def hook(state: str = "trusted", digest: str | None = HASH, name: str = "PreToolUse") -> dict[str, object]:
    return {"hook": name, "state": state, "hash": digest}


def access(**changes: object) -> dict[str, object]:
    return {"item": "codex_local_access", "evidence_source": "bounded local probes", "access": {**ACCESS, **changes}}


class ReadinessCodexTrustTest(ReadinessCase):
    default_host = "codex"
    request_id = "test-codex-trust"

    def test_each_posture_observation_lands_as_an_item_with_evidence(self) -> None:
        item = self.item(posture())
        self.assertEqual("verified", item["status"])
        for fact in ("approval_policy=on-request", "sandbox_mode=workspace-write", "approvals_reviewer=user",
                     "mcp_approval_mode=prompt", "mcp_consent=granted", "external_delegation=allowed"):
            self.assertIn(fact, item["evidence_source"])
        self.assertTrue(item["fingerprints"]["value:posture"].startswith("sha256:"))
        self.assertNotIn("action", item)

    def test_unobservable_or_blocked_posture_never_verifies(self) -> None:
        unknown = self.item(posture(approvals_reviewer="unobservable"))
        self.assertEqual("unknown", unknown["status"])
        self.assertTrue(unknown["action"])
        blocked = self.item(posture(external_delegation="blocked"))
        self.assertEqual("unavailable", blocked["status"])
        self.assertIn("never broadens", blocked["action"])
        self.assertEqual("unknown", self.item(posture(mcp_startup_timeout_sec="unobservable"))["status"])
        default = self.item(posture(mcp_startup_timeout_sec=None, mcp_tool_timeout_sec=None))
        self.assert_item(default, "verified", ("mcp_startup_timeout_sec=default",))

    def test_malformed_posture_is_refused(self) -> None:
        cases = {"policy": {"approval_policy": "always"}, "sandbox": {"sandbox_mode": "off"},
                 "reviewer": {"approvals_reviewer": "bot"}, "mcp mode": {"mcp_approval_mode": "yes"},
                 "consent": {"mcp_consent": True}, "timeout text": {"mcp_tool_timeout_sec": "60"}, "timeout word": {"mcp_tool_timeout_sec": "fast"},
                 "timeout zero": {"mcp_tool_timeout_sec": 0}, "timeout bool": {"mcp_tool_timeout_sec": True},
                 "extra key": {"consent_given": "yes"}}
        for label, change in cases.items():
            with self.subTest(label):
                assert_runner_response(self, self.run_helper([posture(**change)]), "input_error", 2)
        bad = posture()
        bad["status"] = "verified"
        assert_runner_response(self, self.run_helper([bad]), "input_error", 2)

    def test_trusted_hook_records_the_exact_hash(self) -> None:
        item = self.item(hook_trust(hook()))
        self.assert_item(item, "verified", (f"PreToolUse=trusted {HASH}",))
        self.assertTrue(item["fingerprints"]["value:hook_hashes"].startswith("sha256:"))

    def test_untrusted_hook_is_recorded_untrusted_with_its_exact_hash(self) -> None:
        item = self.item(hook_trust(hook(), hook("untrusted", OTHER_HASH, "Stop")))
        self.assert_item(item, "unavailable", (f"Stop=untrusted {OTHER_HASH}",),
                         ("Review and trust the hooks in /hooks", "restart Codex"))

    def test_hook_trust_without_a_readable_hash_is_unknown_and_trust_needs_a_hash(self) -> None:
        item = self.item(hook_trust(hook("unobservable", None)))
        self.assertEqual("unknown", item["status"])
        self.assertEqual("unknown", self.item(hook_trust())["status"])
        assert_runner_response(self, self.run_helper([hook_trust(hook("trusted", None))]), "input_error", 2)
        for bad in ("zz", "a" * 3, HASH + "\nx", "/" + "tmp/x"):
            with self.subTest(bad=bad):
                assert_runner_response(self, self.run_helper([hook_trust(hook("untrusted", bad))]), "input_error", 2)

    def test_duplicate_hook_names_are_refused_and_untrusted_hooks_lead_the_evidence(self) -> None:
        self.refuse_each([hook_trust(hook(), hook(digest=OTHER_HASH))])
        many = [hook(name=f"Hook{n}") for n in range(8)] + [hook("untrusted", OTHER_HASH, "LastHook")]
        self.assert_item(self.item(hook_trust(*many)), "unavailable", (f"LastHook=untrusted {OTHER_HASH}",))

    def test_an_uppercase_digest_is_kept_exactly_as_printed(self) -> None:
        upper = "ABCDEF" * 10 + "ABCD"
        self.assert_item(self.item(hook_trust(hook("trusted", upper))), "verified", (upper,))

    def test_a_partial_egress_policy_is_refused(self) -> None:
        self.refuse_each([access(egress_policy_digest=None), access(egress_policy_ref=None)])
        none = self.item(access(egress_policy_ref=None, egress_policy_digest=None))
        self.assert_item(none, "unknown", ("egress_policy=unobservable",))

    def test_blocked_loopback_is_unavailable_with_the_action(self) -> None:
        item = self.item(access(loopback="blocked"))
        self.assert_item(item, "unavailable", ("loopback=blocked",), ("loopback",))

    def test_leaky_temporary_directory_is_unavailable_with_the_action(self) -> None:
        item = self.item(access(temp_dir="leaky"))
        self.assert_item(item, "unavailable", ("temp_dir=leaky",), ("temporary directory",))
        both = self.item(access(loopback="blocked", temp_dir="leaky"))
        self.assert_item(both, "unavailable", (), ("loopback", "temporary directory"))

    def test_healthy_access_records_the_egress_reference_and_digest_only(self) -> None:
        response = self.run_helper([access()])
        item = self.items(response)["codex_local_access"]
        self.assertEqual("verified", item["status"])
        self.assertIn(f"egress_policy={ACCESS['egress_policy_ref']} {HASH}", item["evidence_source"])
        self.assertEqual("unknown", self.item(access(loopback="unobservable"))["status"])
        self.assertNotIn("entries", json.dumps(response["data"]["record"]))

    def test_malformed_access_is_refused(self) -> None:
        self.refuse_each([access(**change) for change in (
            {"loopback": "maybe"}, {"temp_dir": "ok"}, {"egress_policy_ref": "/" + "etc/policy"},
            {"egress_policy_ref": "a b"}, {"egress_policy_digest": "nothex"}, {"entries": ["x"]})])

    def test_claude_records_the_codex_items_as_not_applicable_and_codex_defaults_to_unknown(self) -> None:
        self.check_codex_only(TRUST_ITEMS, [posture(), hook_trust(hook()), access()])

    def test_scaffold_documents_the_items_on_each_host(self) -> None:
        self.check_documented(TRUST_ITEMS)
        self.assertIn("never broaden", scaffold_step("codex"))


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ReadinessCodexTrustTest)


def main() -> int:
    return run_counted(build_suite(), label="test-readiness-codex-trust")


if __name__ == "__main__":
    raise SystemExit(main())
