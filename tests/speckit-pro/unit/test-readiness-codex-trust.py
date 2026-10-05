#!/usr/bin/env python3
"""Codex approval, trust and sandbox readiness items (ADR 0008): facts about the session, never consent."""

from __future__ import annotations

import json
import sys
import unittest
import unittest.mock
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
LIB_DIR = TEST_DIR.parent / "lib"
sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(TEST_DIR.parents[2] / "speckit-pro"))

from readiness_case import ReadinessCase, scaffold_step  # noqa: E402
from runner_invocation import assert_runner_response  # noqa: E402
from test_result import run_counted  # noqa: E402

TRUST_ITEMS = ("codex_approval_posture", "codex_hook_trust", "codex_local_access")
HASH = "a" * 64
OTHER_HASH = "b" * 64
# Frozen receipts from Codex 0.160.0 hooks/list for the shipped definitions.
SHIPPED_HASHES = {
    "PreToolUse:0:0": "e42169cb205c8adab7c236125f222c127c712e351ecf7cda776bfbcbfa7ce9e0",
    "PreToolUse:1:0": "64c3c89dcaf3998da20e44de2c3c781e817ff626ac2fb1783661cdddc4dde3f3",
    "Stop:0:0": "687b42d9949fa82703e298dab0826652619d2a4f4b22844ec6efabe7e405d261",
}
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


def shipped_trust(**changes: object) -> dict[str, object]:
    entries = [{**hook(digest=value, name=name), "enabled": True} for name, value in SHIPPED_HASHES.items()]
    entries[0].update(changes)
    return hook_trust(*entries)


def access(**changes: object) -> dict[str, object]:
    return {"item": "codex_local_access", "evidence_source": "bounded local probes", "access": {**ACCESS, **changes}}


class ReadinessCodexTrustTest(ReadinessCase):
    default_host = "codex"
    request_id = "test-codex-trust"

    def test_weakened_posture_is_unavailable_without_a_loosening_action(self) -> None:
        item = self.item(posture(approval_policy="never", sandbox_mode="danger-full-access",
                                 approvals_reviewer="auto_review", mcp_approval_mode="approve",
                                 mcp_tool_timeout_sec=86400))
        self.assert_item(item, "unavailable", ("sandbox_mode=danger-full-access",), ("Keep current controls",))

    def test_granular_policy_is_structured_and_preserves_prompt_categories(self) -> None:
        granular = dict.fromkeys(("sandbox_approval", "rules", "mcp_elicitations", "request_permissions",
                                  "skill_approval"), False)
        item = self.item(posture(approval_policy={"granular": granular}))
        self.assert_item(item, "verified", ("sandbox_approval=false", "skill_approval=false"))
        self.refuse_each([posture(approval_policy="granular"),
                          posture(approval_policy={"granular": {"rules": True}})])

    def test_unconfirmed_commands_are_not_promised_as_effective_settings_sources(self) -> None:
        item = self.item(posture(approvals_reviewer="unobservable"))
        self.assertNotIn("with /status and /permissions", item["action"])

    def test_incomplete_or_mismatched_shipped_hook_inventory_never_verifies(self) -> None:
        self.assert_item(self.item(hook_trust(hook())), "unavailable", (), ("shipped",))
        self.assertEqual("unavailable", self.item(shipped_trust(hash=HASH))["status"])
        incomplete = shipped_trust()
        incomplete["hooks"].pop()
        self.assertEqual("unavailable", self.item(incomplete)["status"])

    def test_expected_hashes_match_the_frozen_codex_runtime_receipts(self) -> None:
        from speckit_pro_runner.helpers import readiness_host_items
        self.assertEqual({name: "sha256:" + value for name, value in SHIPPED_HASHES.items()},
                         readiness_host_items.shipped_codex_hooks())
        self.assertEqual("verified", self.item(shipped_trust())["status"])

    def test_disagreeing_codex_hook_observations_are_refused(self) -> None:
        legacy = {"item": "hooks", "evidence_source": "definition review",
                  "hooks": [dict(hook="PreToolUse", defined=True, trust="untrusted")]}
        assert_runner_response(self, self.run_helper([legacy, shipped_trust()]), "input_error", 2)

    def test_legacy_codex_hooks_cannot_verify_without_handler_hashes(self) -> None:
        from speckit_pro_runner.helpers import readiness_host_items
        legacy = {"item": "hooks", "evidence_source": "definition review",
                  "hooks": [dict(hook="Bogus", defined=True, trust="trusted")]}
        _, observed = readiness_host_items.host_item(legacy, "codex", "2026-01-01T00:00:00Z", "revision")
        self.assertEqual("unknown", observed["status"])
        self.assertEqual("unknown", self.items(self.run_helper([legacy]))["hooks"]["status"])

    def test_blocked_delegation_and_denied_consent_actions_preserve_controls(self) -> None:
        for field, value, action in (
            ("external_delegation", "blocked", "Keep external delegation blocked; record the limit and continue independent work."),
            ("mcp_consent", "not_granted", "Keep MCP consent ungranted; record the limit and continue work that does not require MCP."),
        ):
            with self.subTest(field=field):
                item = self.item(posture(**{field: value}))
                self.assertEqual("unavailable", item["status"])
                self.assertEqual(action + " Scaffold never broadens permissions or disables a control.", item["action"])

    def test_redundant_legacy_codex_hooks_cannot_hide_arbitrary_names(self) -> None:
        legacy = {"item": "hooks", "evidence_source": "definition review",
                  "hooks": [dict(hook="Bogus", defined=True, trust="trusted")]}
        assert_runner_response(self, self.run_helper([legacy, shipped_trust()]), "input_error", 2)

    def test_sha256_fingerprints_normalize_case_prefix_and_length(self) -> None:
        from speckit_pro_runner.helpers import readiness_host_items
        self.assertEqual("sha256:" + HASH, readiness_host_items.exact_fingerprint("SHA256:" + HASH.upper()))
        self.refuse_each([hook_trust(hook(digest="a" * 32)), hook_trust(hook(digest="a" * 128))])

    def test_all_hash_fingerprints_ignore_hex_case_and_optional_prefix(self) -> None:
        plain = self.item(shipped_trust())
        prefixed = self.item(shipped_trust(hash="SHA256:" + SHIPPED_HASHES["PreToolUse:0:0"].upper()))
        self.assertEqual(plain["fingerprints"], prefixed["fingerprints"])
        plain_access = self.item(access())
        prefixed_access = self.item(access(egress_policy_digest="SHA256:" + HASH.upper()))
        self.assertEqual(plain_access["fingerprints"], prefixed_access["fingerprints"])

    def test_blocked_loopback_action_preserves_controls(self) -> None:
        item = self.item(access(loopback="blocked"))
        self.assertIn("Keep loopback blocked", item["action"])
        self.assertNotIn("Allow loopback", item["action"])

    def test_caller_temp_health_cannot_override_the_runner_probe(self) -> None:
        from speckit_pro_runner.helpers import readiness_record
        from readiness_case import readiness_request
        for status in ("unavailable", "unknown"):
            probe = {"status": status, "evidence_source": "temporary probe", "observed_at": "2026-01-01T00:00:00Z",
                     "fingerprints": {}, "action": "Inspect temporary storage"}
            with unittest.mock.patch.object(readiness_record, "observe_local_capability", return_value=probe):
                record = readiness_record.build_record(readiness_request([access()], "codex")["inputs"], self.root)
            self.assertEqual(status, record["items"]["codex_local_access"]["status"])

    def test_codex_hook_items_share_one_trust_observation(self) -> None:
        response = self.run_helper([hook_trust(hook("untrusted"))])
        items = self.items(response)
        self.assertEqual(items["codex_hook_trust"], items["hooks"])

    def test_claude_parity_check_rejects_a_missing_required_item(self) -> None:
        response = self.run_helper([], "claude")
        del response["data"]["record"]["items"]["codex_hook_trust"]
        with unittest.mock.patch.object(self, "run_helper", return_value=response):
            with self.assertRaises((KeyError, AssertionError)):
                self.check_codex_only(TRUST_ITEMS, [])

    def test_allowlists_reject_policy_variants_and_padded_hook_names(self) -> None:
        self.refuse_each([posture(**{field: value}) for field, value in (
            ("approval_policy", "never-extra"), ("approval_policy", "NEVER"),
            ("sandbox_mode", "workspace-write-extra"), ("sandbox_mode", "WORKSPACE-WRITE"),
            ("mcp_approval_mode", "prompt-extra"), ("mcp_approval_mode", "PROMPT"))])
        self.refuse_each([hook_trust(hook(name=" PreToolUse ")), hook_trust(hook(name="PreToolUse\n"))])

    def test_unknown_probe_never_defaults_to_a_git_command_exemption(self) -> None:
        from speckit_pro_runner.helpers import readiness_host_items
        from speckit_pro_runner.strict_input import SelectionError
        with self.assertRaises(SelectionError):
            readiness_host_items.allow_rule_texts([{"probe": "git status-extra", "outcome": "denied"}], "python3")

    def test_exact_names_keep_the_credential_filter(self) -> None:
        from speckit_pro_runner.helpers import readiness_host_items
        from speckit_pro_runner.strict_input import SelectionError
        with self.assertRaises(SelectionError):
            readiness_host_items.name_text("ghp_" + "a" * 35 + "1", "hook name")

    def test_disabled_or_unobservable_hook_enablement_never_verifies(self) -> None:
        self.assertEqual("unavailable", self.item(shipped_trust(enabled=False))["status"])
        self.assertEqual("unknown", self.item(shipped_trust(enabled=None))["status"])

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
        item = self.item(shipped_trust())
        self.assert_item(item, "verified", (f"PreToolUse:0:0=trusted {SHIPPED_HASHES['PreToolUse:0:0']}",))
        self.assertTrue(item["fingerprints"]["value:hook_hashes"].startswith("sha256:"))

    def test_untrusted_hook_is_recorded_untrusted_with_its_exact_hash(self) -> None:
        item = self.item(shipped_trust(state="untrusted"))
        self.assert_item(item, "unavailable", (f"PreToolUse:0:0=untrusted {SHIPPED_HASHES['PreToolUse:0:0']}",),
                         ("Review and trust the hooks in /hooks", "restart Codex"))

    def test_hook_trust_without_a_readable_hash_is_unknown_and_trust_needs_a_hash(self) -> None:
        item = self.item(shipped_trust(state="unobservable", hash=None))
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
        upper = SHIPPED_HASHES["PreToolUse:0:0"].upper()
        item = self.item(shipped_trust(hash="SHA256:" + upper))
        self.assert_item(item, "verified", (upper,))
        self.assertEqual("sha256:" + upper.lower(), item["fingerprints"]["hook:PreToolUse:0:0"])

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
