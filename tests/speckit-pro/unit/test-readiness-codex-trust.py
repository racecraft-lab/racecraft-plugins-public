#!/usr/bin/env python3
"""Codex approval, trust and sandbox readiness items (ADR 0008): facts about the session, never consent."""

from __future__ import annotations

import itertools
import json
import sys
import unittest
import unittest.mock
from collections.abc import Callable
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
# Every effective control beyond the eight-field summary, each at its conservative value.
CONTROLS = {"workspace_network_access": "disabled", "workspace_writable_roots": "none",
            "workspace_slash_tmp": "excluded", "workspace_tmpdir": "excluded", "permission_profile": "none",
            "web_search": "disabled", "web_search_tool": "disabled", "app_approvals_reviewer": "user",
            "auto_review_policy": "unset", "app_tool_approval": "prompt", "app_destructive_tools": "disabled",
            "app_open_world_tools": "disabled", "mcp_tool_approval": "prompt", "plugin_mcp_tool_approval": "none"}
# Every configuration key set in any effective layer, as dotted TOML key paths: inert, judged by a summary
# fact or control, or at its conservative value.
SETTINGS = {"model": "gpt-6.1-sol", "model_reasoning_effort": "high", 'projects."repo".trust_level': "untrusted",
            "check_for_update_on_startup": False, "features.hooks": False, "approval_policy": "on-request",
            "sandbox_mode": "workspace-write", "sandbox_workspace_write.network_access": False}
POSTURE = {"approval_policy": "on-request", "sandbox_mode": "workspace-write", "approvals_reviewer": "user",
           "mcp_approval_mode": "prompt", "mcp_consent": "granted", "mcp_startup_timeout_sec": 10,
           "mcp_tool_timeout_sec": 60, "external_delegation": "allowed", "controls": CONTROLS, "settings": SETTINGS}
# Security finding F1263-6fd5beee: each named variant and the control value that represents it.
BROADENING_CONTROLS = {
    "workspace-write network access": [("workspace_network_access", "enabled")],
    "extra workspace-write writable roots": [("workspace_writable_roots", "added")],
    "/tmp left writable": [("workspace_slash_tmp", "writable")],
    "TMPDIR left writable": [("workspace_tmpdir", "writable")],
    "default_permissions or custom permission profile": [("permission_profile", value)
                                                         for value in ("custom", "workspace", "danger-full-access")],
    "web search external-data path": [("web_search", "indexed"), ("web_search", "live"),
                                      ("web_search_tool", "enabled")],
    "app approval reviewer or auto-review policy": [("app_approvals_reviewer", "auto_review"),
                                                    ("auto_review_policy", "set")],
    "app tool approval, destructive and open-world controls": [
        *(("app_tool_approval", mode) for mode in ("auto", "writes", "approve")),
        ("app_destructive_tools", "enabled"), ("app_open_world_tools", "enabled")],
    "MCP server and per-tool approval beside a prompt summary": [("mcp_tool_approval", mode)
                                                                 for mode in ("auto", "writes", "approve")],
    "plugin-provided MCP tool approval": [("plugin_mcp_tool_approval", mode) for mode in ("auto", "writes", "approve")],
}
# Security finding F1263-946bd436: each named variant as the settings that represent it.
ENVIRONMENT_VARIANTS = {
    "set.PATH": {"shell_environment_policy.set.PATH": "repo-bin:usr-bin"},
    "set.PYTHONPATH": {"shell_environment_policy.set.PYTHONPATH": "repo-lib"},
    "inherit=all with ignore_default_excludes=true": {"shell_environment_policy.inherit": "all",
                                                      "shell_environment_policy.ignore_default_excludes": True},
    "allow_login_shell=true": {"allow_login_shell": True},
    "experimental_use_profile=true": {"shell_environment_policy.experimental_use_profile": True},
}
# The class: a key the model does not know, at the top level or nested under a table it knows.
UNKNOWN_SETTINGS = {
    "an unknown future key": {"future_escape_hatch": True},
    "an unknown key under shell_environment_policy": {"shell_environment_policy.future_inherit": "everything"},
    "an unknown key under sandbox_workspace_write": {"sandbox_workspace_write.future_roots": ["repo"]},
    "an unknown key under tui": {"tui.future_option": True},
    "an unknown key under a modeled MCP server": {'mcp_servers."docs".future_mode': "auto"},
}
# Filters that only remove inherited variables never add or replace one, so they may verify.
NARROWING_SETTINGS = {"shell_environment_policy.inherit": "core",
                      "shell_environment_policy.ignore_default_excludes": False,
                      'shell_environment_policy.filters."*TOKEN*"': "exclude",
                      'shell_environment_policy.filters."HOME"': "include",
                      "shell_environment_policy.exclude": ["AWS_*"], "shell_environment_policy.include_only": ["PATH"],
                      "shell_environment_policy.experimental_use_profile": False, "allow_login_shell": False}
# What the scaffold step promises about the settings inventory, reconciliation and skipped controls.
SETTINGS_PROMISES = ("are the same key", "a key named twice", "also a table holding",
                     "A contradiction makes the posture `unavailable`", "one nested under a known table",
                     "reconciled with its aggregate before the aggregate counts", "it rules out `none`",
                     "`features.apps` to false; another control's value never makes a control inapplicable",
                     "`auto_review` is conservative only under `never` or a granular policy with every category false",
                     "one key table", "`apps._default` takes only `enabled`",
                     "such as `apps._default.default_tools_enabled`, switches nothing off",
                     "`_default` is reserved only as an app id",
                     "counts only when `settings` configures that marketplace",
                     "`features.plugins` false", "`features.codex_hooks` false", "`features.remote_plugin` false",
                     "`project_doc_max_bytes` a whole number at most 32768")
LEGACY_HOOK_ACTION = ("Send a complete codex_hook_trust observation that verifies each hook's identity and exact hash "
                      "against the shipped definitions, then rerun scaffold. Never trust a hook that is not "
                      "verified. Scaffold never broadens permissions or disables a control.")
ACCESS = {"loopback": "allowed", "temp_dir": "healthy", "egress_policy_ref": "egress-policy",
          "egress_policy_digest": HASH}


def posture(**changes: object) -> dict[str, object]:
    return {"item": "codex_approval_posture", "evidence_source": "codex session settings",
            "posture": {**POSTURE, **changes}}


def controls(**changes: object) -> dict[str, object]:
    return posture(controls={**CONTROLS, **changes})


def settings(**changes: object) -> dict[str, object]:
    return posture(settings={**SETTINGS, **changes})


def granular_posture(granular: dict[str, bool]) -> dict[str, object]:
    """A granular approval policy with the inventory keys that set it."""
    inventory = {key: value for key, value in SETTINGS.items() if key != "approval_policy"}
    return posture(approval_policy={"granular": granular}, settings={
        **inventory, **{f"approval_policy.granular.{name}": flag for name, flag in granular.items()}})


def hook_trust(*entries: dict[str, object]) -> dict[str, object]:
    return {"item": "codex_hook_trust", "evidence_source": "/hooks review", "hooks": list(entries)}


def hook(state: str = "trusted", digest: str | None = HASH, name: str = "PreToolUse") -> dict[str, object]:
    return {"hook": name, "state": state, "hash": digest}


def shipped_trust(**changes: object) -> dict[str, object]:
    entries = [{**hook(digest=value, name=name), "enabled": True} for name, value in SHIPPED_HASHES.items()]
    entries[0].update(changes)
    return hook_trust(*entries)


def assert_each(test: ReadinessCase, cases: dict[str, dict[str, object]], status: str, evidence: tuple[str, ...],
                build: Callable[[dict[str, object]], dict[str, object]] = lambda changes: posture(settings=changes),
                action: tuple[str, ...] = ()) -> None:
    """Each named case's observation, built from its settings, records `status` with `evidence`."""
    for case, changes in cases.items():
        with test.subTest(case=case):
            test.assert_item(test.item(build(changes)), status, evidence, action)


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
        item = self.item(granular_posture(granular))
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
        # The overlap refusal runs before any hook-name comparison, so a legacy
        # observation with an arbitrary name is refused the same way.
        for name, trust in (("PreToolUse", "untrusted"), ("Bogus", "trusted")):
            with self.subTest(hook=name):
                legacy = {"item": "hooks", "evidence_source": "definition review",
                          "hooks": [dict(hook=name, defined=True, trust=trust)]}
                assert_runner_response(self, self.run_helper([legacy, shipped_trust()]), "input_error", 2)
        for empty in ({"item": "hooks", "evidence_source": "definition review", "hooks": []},
                      {"item": "hooks", "evidence_source": "definition review"}):
            with self.subTest(empty=empty):
                assert_runner_response(self, self.run_helper([empty, shipped_trust()]), "input_error", 2)
                self.assertEqual("unknown", self.items(self.run_helper([empty]))["hooks"]["status"])

    def test_legacy_codex_hooks_cannot_verify_without_handler_hashes(self) -> None:
        from speckit_pro_runner.helpers import readiness_host_items
        legacy = {"item": "hooks", "evidence_source": "definition review",
                  "hooks": [dict(hook="Bogus", defined=True, trust="trusted")]}
        _, observed = readiness_host_items.host_item(legacy, "codex", "2026-01-01T00:00:00Z", "revision")
        self.assertEqual("unknown", observed["status"])
        self.assertEqual("unknown", self.items(self.run_helper([legacy]))["hooks"]["status"])
        legacy["hooks"][0]["trust"] = "untrusted"  # an unverified hook is never told to be trusted
        self.assertEqual(("unavailable", LEGACY_HOOK_ACTION), tuple(
            self.items(self.run_helper([legacy]))["hooks"][key] for key in ("status", "action")))

    def test_blocked_delegation_and_denied_consent_actions_preserve_controls(self) -> None:
        for field, value, action in (
            ("external_delegation", "blocked", "Keep external delegation blocked; record the limit and continue independent work."),
            ("mcp_consent", "not_granted", "Keep MCP consent ungranted; record the limit and continue work that does not require MCP."),
        ):
            with self.subTest(field=field):
                item = self.item(posture(**{field: value}))
                self.assertEqual("unavailable", item["status"])
                self.assertEqual(action + " Scaffold never broadens permissions or disables a control.", item["action"])

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

    def test_long_posture_source_preserves_all_observed_facts(self) -> None:
        source = ("Effective running-thread approval, sandbox, reviewer and MCP settings observed "
                  "from the active Codex configuration source")
        granular = dict.fromkeys(("sandbox_approval", "rules", "mcp_elicitations", "request_permissions",
                                  "skill_approval"), False)
        for label in (source, source.ljust(400, ".")):
            with self.subTest(source_length=len(label)):
                observation = granular_posture(granular)
                observation["evidence_source"] = label
                item = self.item(observation)
                self.assertEqual("verified", item["status"])
                self.assertTrue(item["evidence_source"].startswith("Effective running-thread"))
                for fact in ("sandbox_approval=false", "rules=false", "mcp_elicitations=false",
                             "request_permissions=false", "skill_approval=false", "sandbox_mode=workspace-write",
                             "approvals_reviewer=user", "mcp_approval_mode=prompt", "mcp_consent=granted",
                             "external_delegation=allowed", "mcp_startup_timeout_sec=10", "mcp_tool_timeout_sec=60"):
                    self.assertIn(fact, item["evidence_source"])
                self.assertLessEqual(len(item["evidence_source"]), 400)

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

    def test_untrusted_hook_without_an_observed_hash_is_never_recommended_for_trust(self) -> None:
        """Daybreak F1263-f9a03fc7: no trust recommendation without the exact hash under review."""
        omitted = shipped_trust(state="untrusted")
        del omitted["hooks"][0]["hash"]  # type: ignore[index]
        for label, observation in (("omitted hash", omitted), ("null hash", shipped_trust(state="untrusted", hash=None)),
                                   ("null hash, unobservable enablement",
                                    shipped_trust(state="untrusted", hash=None, enabled=None))):
            with self.subTest(label):
                item = self.item(observation)
                self.assertEqual(("unavailable", LEGACY_HOOK_ACTION), (item["status"], item["action"]))

    def test_mixed_hook_evidence_without_every_hash_is_never_recommended_for_trust(self) -> None:
        """Daybreak F1263-f9a03fc7, residual: a hash-bound untrusted hook beside a hashless unobservable one."""
        for label, hashless in (("omitted hash", {}), ("null hash", {"hash": None}),
                                ("omitted hash, unobservable enablement", {"enabled": None}),
                                ("null hash, unobservable enablement", {"hash": None, "enabled": None})):
            observation = shipped_trust(state="untrusted")
            second = observation["hooks"][1]  # type: ignore[index]
            second.pop("hash")
            second.update({"state": "unobservable", **hashless})
            with self.subTest(label):
                item = self.item(observation)
                self.assertEqual(("unavailable", LEGACY_HOOK_ACTION), (item["status"], item["action"]))
                self.assertNotIn("Review and trust", item["action"])

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



class ReadinessCodexPostureControlsTest(ReadinessCase):
    """Security finding F1263-6fd5beee: controls beyond the eight-field summary never hide behind `verified`."""

    default_host = "codex"
    request_id = "test-codex-posture-controls"

    def test_eight_field_posture_without_its_controls_never_verifies(self) -> None:
        legacy = posture()
        del legacy["posture"]["controls"]  # type: ignore[attr-defined]
        self.assert_item(self.item(legacy), "unknown", ("controls=missing",), ("posture control",))
        for name in CONTROLS:
            partial = posture(controls={key: value for key, value in CONTROLS.items() if key != name})
            with self.subTest(missing=name):
                self.assertEqual("unknown", self.item(partial)["status"])
            with self.subTest(unobservable=name):
                self.assertEqual("unknown", self.item(controls(**{name: "unobservable"}))["status"])
        self.assertEqual("unknown", self.item({"item": "codex_approval_posture",
                                               "evidence_source": "codex session settings"})["status"])

    def test_each_broadening_control_is_unavailable_never_verified(self) -> None:
        for variant, changes in BROADENING_CONTROLS.items():
            for name, value in changes:
                with self.subTest(variant=variant, control=name, value=value):
                    self.assert_item(self.item(controls(**{name: value})), "unavailable",
                                     ("controls=1 outside",), ("Keep current controls", "never broadens"))

    def test_a_prompt_summary_cannot_hide_a_broader_per_tool_approval(self) -> None:
        contradictory = controls(mcp_tool_approval="auto", plugin_mcp_tool_approval="approve")
        self.assertEqual("prompt", contradictory["posture"]["mcp_approval_mode"])  # type: ignore[index]
        self.assert_item(self.item(contradictory), "unavailable", ("mcp_approval_mode=prompt", "controls=2 outside"))
        assert_runner_response(self, self.run_helper([posture(), controls(web_search="live")]), "input_error", 2)

    def test_controls_outside_their_scope_do_not_block_a_conservative_posture(self) -> None:
        self.assert_item(self.item(posture()), "verified", ("controls=conservative",))
        self.assertEqual("verified", self.item(controls(web_search="cached", permission_profile="read-only",
                                                        app_tool_approval="none", mcp_tool_approval="none"))["status"])
        workspace = {name: "writable" for name in ("workspace_slash_tmp", "workspace_tmpdir")}
        read_only = posture(sandbox_mode="read-only", settings={**SETTINGS, "sandbox_mode": "read-only"}, controls={
            **CONTROLS, **workspace, "workspace_network_access": "enabled", "workspace_writable_roots": "unobservable"})
        self.assertEqual("verified", self.item(read_only)["status"])
        # The app tool hints are inert only when the inventory switches apps off.
        hints = {**CONTROLS, "app_tool_approval": "none", "app_destructive_tools": "enabled",
                 "app_open_world_tools": "unobservable"}
        self.assertEqual("verified", self.item(posture(controls=hints, settings={
            **SETTINGS, "features.apps": False}))["status"])
        self.assertEqual("unavailable", self.item(controls(**workspace))["status"])
        self.assertEqual("unknown", self.item(posture(sandbox_mode="unobservable"))["status"])
        self.assertEqual("unavailable", self.item(posture(sandbox_mode="unobservable", controls={
            **CONTROLS, "workspace_network_access": "enabled"}))["status"])

    def test_malformed_posture_controls_are_refused(self) -> None:
        self.refuse_each([posture(controls=bad) for bad in (
            None, [], "none", {**CONTROLS, "network_access": "disabled"}, {**CONTROLS, "web_search": "LIVE"},
            {**CONTROLS, "workspace_network_access": True}, {**CONTROLS, "other_overrides": "none"},
            {**CONTROLS, "workspace_writable_roots": "/" + "tmp"})])

    def test_scaffold_documents_every_posture_control_and_its_values(self) -> None:
        from speckit_pro_runner.helpers import readiness_host_items
        self.assertEqual(set(CONTROLS), set(readiness_host_items.POSTURE_CONTROLS))
        step = scaffold_step("codex")
        for name, (safe, broad) in readiness_host_items.POSTURE_CONTROLS.items():
            with self.subTest(control=name):
                quoted = [f'"{value}"' for value in (*safe, *broad)]
                self.assertIn(f'"{name}": ' + ", ".join(quoted[:-1]) + " or " + quoted[-1], step)


class ReadinessCodexPostureSettingsTest(ReadinessCase):
    """Security finding F1263-946bd436: a setting the model does not account for never hides behind `verified`."""

    default_host = "codex"
    request_id = "test-codex-posture-settings"

    def test_each_environment_variant_is_unavailable_never_verified(self) -> None:
        for variant, changes in ENVIRONMENT_VARIANTS.items():
            with self.subTest(variant=variant):
                self.assert_item(self.item(settings(**changes)), "unavailable",
                                 (f"settings={len(changes)} outside",), ("Keep current controls", "never broadens"))
            with self.subTest(variant=variant, value="unobservable"):
                unread = dict.fromkeys(changes, "unobservable")
                self.assert_item(self.item(settings(**unread)), "unknown", (f"{len(changes)} unobservable",))

    def test_an_unknown_key_is_unavailable_when_observed_and_unknown_when_not(self) -> None:
        for case, changes in UNKNOWN_SETTINGS.items():
            with self.subTest(case=case):
                self.assert_item(self.item(settings(**changes)), "unavailable", ("settings=1 outside",))
            with self.subTest(case=case, value="unobservable"):
                self.assertEqual("unknown", self.item(settings(**dict.fromkeys(changes, "unobservable")))["status"])

    def test_narrowing_only_environment_filters_may_verify(self) -> None:
        self.assert_item(self.item(settings(**NARROWING_SETTINGS)), "verified", ("settings=accounted",))
        self.assertEqual("verified", self.item(settings(**{"shell_environment_policy.inherit": "none"}))["status"])

    def test_inert_and_modeled_settings_verify_and_conservative_controls_still_judge_them(self) -> None:
        self.assert_item(self.item(posture()), "verified", ("controls=conservative", "settings=accounted"))
        self.assertEqual("verified", self.item(posture(settings={}))["status"])
        # A key a control models is judged by that control, so its value here cannot verify a broader control.
        broad = controls(workspace_network_access="enabled")
        broad["posture"]["settings"] = {**SETTINGS, "sandbox_workspace_write.network_access": True}  # type: ignore[index]
        self.assertEqual("unavailable", self.item(broad)["status"])

    def test_missing_or_unreadable_settings_never_verify(self) -> None:
        legacy = posture()
        del legacy["posture"]["settings"]  # type: ignore[attr-defined]
        self.assert_item(self.item(legacy), "unknown", ("settings=missing",), ("every configuration key",))
        self.assert_item(self.item(posture(settings="unobservable")), "unknown", ("settings=unobservable",))

    def test_malformed_settings_are_refused(self) -> None:
        self.refuse_each([posture(settings=bad) for bad in (
            None, [], "none", {"shell_environment_policy": {"inherit": "all"}},
            {"shell_environment_policy.set": {"PATH": "repo-bin"}}, {"": True}, {"a..b": True}, {" model": "x"},
            {'a."b': True}, {"a.b\n": True}, {"allow_login_shell": "yes"}, {"allow_login_shell": 1},
            {"shell_environment_policy.inherit": "everything"}, {"shell_environment_policy.include_only": "PATH"},
            {"shell_environment_policy.include_only": [1]}, {'shell_environment_policy.filters."X"': "allow"},
            {"shell_environment_policy.set.PATH": 1}, {f"key{n}": True for n in range(600)})])

    def test_observed_values_and_key_names_never_reach_the_record(self) -> None:
        response = self.run_helper([settings(**ENVIRONMENT_VARIANTS["set.PATH"])])
        record = json.dumps(response["data"]["record"])
        self.assertNotIn("repo-bin", record)
        self.assertNotIn("shell_environment_policy", record)
        item = self.items(response)["codex_approval_posture"]
        self.assertTrue(item["fingerprints"]["value:posture_settings"].startswith("sha256:"))
        self.assertNotEqual(item["fingerprints"]["value:posture_settings"],
                            self.item(posture())["fingerprints"]["value:posture_settings"])

    def test_scaffold_documents_the_settings_inventory_and_each_conservative_value(self) -> None:
        from speckit_pro_runner.helpers import readiness_posture_settings
        step = scaffold_step("codex")
        self.assertIn('"settings": {"<dotted key>": <value>', step)
        for key in readiness_posture_settings.CONSERVATIVE_SETTINGS:
            with self.subTest(key=key):
                self.assertIn(f"`{key}`", step)
        for promise in SETTINGS_PROMISES:
            with self.subTest(promise=promise):
                self.assertIn(promise, " ".join(step.split()))


# Cross-host review of 90c516e01 and Daybreak F1263-fcc0990b: a modeled key must agree with the summary fact or
# control that models it. Each case alone contradicts the conservative summary, so the posture is unavailable.
CONTRADICTIONS = {
    "network access beside a disabled control": {"sandbox_workspace_write.network_access": True},
    "danger-full-access beside workspace-write": {"sandbox_mode": "danger-full-access"},
    "approval policy": {"approval_policy": "never"},
    "a granular category beside on-request": {"approval_policy.granular.rules": True},
    "approvals reviewer": {"approvals_reviewer": "auto_review"},
    "writable roots": {"sandbox_workspace_write.writable_roots": ["repo"]},
    "/tmp writable": {"sandbox_workspace_write.exclude_slash_tmp": False},
    "TMPDIR writable": {"sandbox_workspace_write.exclude_tmpdir_env_var": False},
    "a built-in permission profile": {"default_permissions": ":workspace"},
    "a custom permission profile": {"default_permissions": "builder"},
    "a leaf of the selected custom profile": {"default_permissions": "builder",
                                             'permissions."builder".network.enabled': True},
    "a profile named like a built-in": {'permissions.":workspace".network.enabled': True},
    "web search mode": {"web_search": "live"},
    "web search tool": {"tools.web_search": True},
    "a web search tool table": {"tools.web_search.context_size": "high"},
    "legacy web search": {"features.web_search": True},
    "legacy live web search": {"features.web_search_request": True},
    "legacy cached web search beside disabled": {"features.web_search_cached": True},
    "apps off beside a prompting app tool": {"features.apps": False},
    "an app reviewer": {'apps."drive".approvals_reviewer': "auto_review"},
    "an app default approval": {'apps."drive".default_tools_approval_mode': "auto"},
    "an app tool approval": {'apps."drive".tools."upload".approval_mode': "writes"},
    "destructive app tools": {'apps."drive".destructive_enabled': True},
    "open-world app tools": {'apps."drive".open_world_enabled': True},
    "auto-review policy": {"auto_review.policy": "approve reads"},
    "auto-review extra policy": {"auto_review.extra_policy": "approve reads"},
    "an MCP default approval": {'mcp_servers."docs".default_tools_approval_mode': "approve"},
    "an MCP tool approval": {'mcp_servers."docs".tools."search".approval_mode': "auto"},
    "an MCP startup timeout": {'mcp_servers."docs".startup_timeout_sec': 30},
    "an MCP startup timeout in milliseconds": {'mcp_servers."docs".startup_timeout_ms': 30000},
    "an MCP tool timeout": {'mcp_servers."docs".tool_timeout_sec': 120},
    "a plugin MCP default approval": {'plugins."kit".mcp_servers."docs".default_tools_approval_mode': "auto"},
    "a plugin MCP tool approval": {'plugins."kit".mcp_servers."docs".tools."search".approval_mode': "writes"},
}
# Modeled keys whose values agree with the conservative summary, or cannot act, so the posture still verifies.
AGREEING_SETTINGS = {
    "sandbox_workspace_write.exclude_slash_tmp": True, "sandbox_workspace_write.exclude_tmpdir_env_var": True,
    "sandbox_workspace_write.writable_roots": [], "web_search": "disabled", "tools.web_search": False,
    "features.web_search_request": False, 'apps."drive".approvals_reviewer': "user",
    'apps."drive".default_tools_approval_mode': "prompt", 'apps."drive".tools."upload".approval_mode': "prompt",
    'apps."drive".destructive_enabled': False, 'apps."off".enabled': False,
    'apps."off".default_tools_approval_mode': "auto", 'mcp_servers."docs".default_tools_approval_mode': "prompt",
    'mcp_servers."docs".startup_timeout_sec': 10, 'mcp_servers."docs".tool_timeout_sec': 60,
    'mcp_servers."docs".enabled_tools': ["search"], 'permissions."spare".network.enabled': True,
}
# Daybreak F1263-d253526b: a contributor-selected Git marketplace beside an enabled plugin.
GIT_MARKETPLACE = {'marketplaces."contrib".source': "https://example.invalid/contrib.git",
                   'marketplaces."contrib".source_type': "git", 'marketplaces."contrib".ref': "main",
                   'marketplaces."contrib".sparse_paths': ["plugins/kit"]}
ENABLED_PLUGIN = {'plugins."kit@contrib".enabled': True}
# Keys that select external content, activate configuration or hooks, or send data: never inert.
ACTIVATING_SETTINGS = {**GIT_MARKETPLACE, **ENABLED_PLUGIN, "features.hooks": True,
                       'projects."repo".trust_level': "trusted", "check_for_update_on_startup": True}


def sample_key(rule: str) -> str:
    """A concrete key path for a rule: each user-named segment becomes one quoted name."""
    return rule.replace("*", '"x"')


class ReadinessCodexPostureEvidenceTest(ReadinessCase):
    """Cross-host review of 90c516e01: the inventory is the evidence, and the posture verifies only when it proves it."""

    default_host = "codex"
    request_id = "test-codex-posture-evidence"

    def test_one_canonical_path_per_key_whatever_the_order(self) -> None:
        bare, quoted = "allow_login_shell", '"allow_login_shell"'
        self.refuse_each([posture(settings={bare: True, quoted: False}), posture(settings={quoted: False, bare: True}),
                          posture(settings={"shell_environment_policy.inherit": "core",
                                            '"shell_environment_policy".inherit': "all",
                                            'shell_environment_policy."inherit"': "none"}),
                          posture(settings={"tools.web_search": False, "tools.web_search.context_size": "low"}),
                          posture(settings={"'allow_login_shell'": False}),
                          posture(settings={"shell_environment_policy . inherit": "core"})])
        self.assertEqual("unavailable", self.item(posture(settings={bare: True}))["status"])

    def test_a_quoted_segment_holding_a_dot_is_one_segment(self) -> None:
        self.assert_item(self.item(settings(**{'"sandbox_workspace_write.network_access"': False})), "unavailable",
                         ("settings=1 outside",))
        self.assertEqual("verified", self.item(settings(**{
            'shell_environment_policy.filters."*.TOKEN"': "exclude"}))["status"])

    def test_no_wildcard_lets_an_unknown_descendant_verify(self) -> None:
        for key in ("tools.web_search.future_escape_hatch", "permissions.profile.future_escape_hatch",
                    'permissions."profile".network.future.escape', 'mcp_servers."docs".tools."search".future_mode',
                    "tools.web_search.location.future"):
            with self.subTest(key=key):
                self.assert_item(self.item(settings(**{key: True})), "unavailable", ("settings=1 outside",))
            with self.subTest(key=key, value="unobservable"):
                self.assert_item(self.item(settings(**{key: "unobservable"})), "unknown", ("1 unobservable",))

    def test_rules_are_exact_and_belong_to_one_list(self) -> None:
        from speckit_pro_runner.helpers import readiness_posture_settings as module
        rules = {"modeled": list(module.MODELED_PATTERNS), "inert": list(module.INERT_SETTINGS),
                 "conservative": list(module.CONSERVATIVE_PATTERNS)}
        for name, patterns in rules.items():
            for rule in patterns:
                self.assertNotIn("**", rule, name)
                for other, other_patterns in rules.items():
                    if other != name:
                        self.assertFalse(any(module.matches(rule, seen) or module.matches(seen, rule)
                                             for seen in other_patterns), (name, rule, other))

    def test_a_modeled_value_that_contradicts_its_summary_is_unavailable(self) -> None:
        assert_each(self, CONTRADICTIONS, "unavailable", ("settings=0 outside, ", " contradicted"),
                    action=("Keep current controls",))

    def test_a_modeled_value_that_agrees_with_its_summary_verifies(self) -> None:
        self.assert_item(self.item(settings(**AGREEING_SETTINGS)), "verified", ("settings=accounted",))
        self.assertEqual("verified", self.item(posture(
            settings={"default_permissions": ":read-only"},
            controls={**CONTROLS, "permission_profile": "read-only"}))["status"])
        granular = dict.fromkeys(("sandbox_approval", "rules", "mcp_elicitations", "request_permissions",
                                  "skill_approval"), True)
        self.assertEqual("verified", self.item(posture(approval_policy={"granular": granular}, settings={
            f"approval_policy.granular.{name}": flag for name, flag in granular.items()}))["status"])
        self.assertEqual("unavailable", self.item(posture(approval_policy={"granular": granular}, settings={
            "approval_policy.granular.rules": False}))["status"])
        # A workspace-write key cannot act under a read-only sandbox, so its control is not compared.
        self.assertEqual("verified", self.item(posture(sandbox_mode="read-only", settings={
            "sandbox_mode": "read-only", "sandbox_workspace_write.network_access": True}))["status"])

    def test_an_unreadable_modeled_value_is_unknown(self) -> None:
        from speckit_pro_runner.helpers import readiness_posture_settings
        for rule in readiness_posture_settings.MODELED_SETTINGS:
            with self.subTest(key=sample_key(rule)):
                self.assert_item(self.item(posture(settings={sample_key(rule): "unobservable"})), "unknown",
                                 ("settings=0 outside, 0 contradicted, 1 unobservable",))

    def test_a_malformed_modeled_value_is_refused(self) -> None:
        self.refuse_each([posture(settings=bad) for bad in (
            {"sandbox_workspace_write.network_access": "yes"}, {"sandbox_mode": "everything"},
            {'mcp_servers."docs".tool_timeout_sec': True}, {'apps."drive".default_tools_approval_mode': "always"},
            {"sandbox_workspace_write.writable_roots": "repo"})])

    def test_plugin_supply_chain_and_activation_keys_are_never_inert(self) -> None:
        from speckit_pro_runner.helpers import readiness_posture_settings as module
        inert = module.INERT_SETTINGS
        for key in ACTIVATING_SETTINGS:
            path = module.key_path(key)
            self.assertFalse(any(module.matches(rule, path) for rule in inert), key)
        self.assert_item(self.item(settings(**GIT_MARKETPLACE, **ENABLED_PLUGIN)), "unavailable",
                         ("settings=5 outside",))
        for key, value in ACTIVATING_SETTINGS.items():
            with self.subTest(key=key):
                self.assert_item(self.item(settings(**{key: value})), "unavailable", ("settings=1 outside",))
        unread = dict.fromkeys(GIT_MARKETPLACE, "unobservable")
        self.assert_item(self.item(settings(**unread, **ENABLED_PLUGIN)), "unavailable",
                         ("settings=1 outside, 0 contradicted, 4 unobservable",))
        self.assertEqual("unknown", self.item(settings(**unread))["status"])
        local = {'marketplaces."local".source': "local-marketplace", 'marketplaces."local".source_type': "local"}
        self.assertEqual("unavailable", self.item(settings(**local))["status"])
        for key, value in (("features.plugins", False), ("features.hooks", False),
                           ('projects."repo".trust_level', "untrusted"), ("check_for_update_on_startup", False)):
            with self.subTest(key=key, value=value):
                self.assertEqual("verified", self.item(settings(**{key: value}))["status"])
        record = json.dumps(self.run_helper([settings(**GIT_MARKETPLACE)])["data"]["record"])
        self.assertNotIn("example.invalid", record)
        self.assertNotIn("contrib", record)


# Cross-host review of d2db22fc8: an aggregate control is never trusted ahead of the explicit inventory it
# summarizes. The review's probe: explicit app activation behind app_tool_approval="none".
APP_ACTIVATION = {"features.apps": True, 'apps."drive".enabled': True, 'apps."drive".default_tools_enabled': True,
                  'apps."drive".tools."upload".enabled': True, 'apps."drive".tools."upload".approval_mode': "prompt",
                  'apps."drive".destructive_enabled': True, 'apps."drive".open_world_enabled': True}
NO_TOOLS = {**CONTROLS, "app_tool_approval": "none", "mcp_tool_approval": "none", "plugin_mcp_tool_approval": "none"}


def no_tools(changes: dict[str, object]) -> dict[str, object]:
    """Every tool approval aggregate `none` beside the conservative inventory plus `changes`."""
    return posture(controls=NO_TOOLS, settings={**SETTINGS, **changes})

# Each explicit key alone implies an enabled tool, or a tool hint, that a `none` aggregate denies.
AGGREGATE_CONTRADICTIONS = {
    "an enabled app": {'apps."drive".enabled': True},
    "an app's default-enabled tools": {'apps."drive".default_tools_enabled': True},
    "an enabled app tool": {'apps."drive".tools."upload".enabled': True},
    "a prompting app tool": {'apps."drive".tools."upload".approval_mode': "prompt"},
    "a prompting app default": {'apps."drive".default_tools_approval_mode': "prompt"},
    "the default app enabled": {'apps."_default".enabled': True},
    "destructive app tools": {'apps."drive".destructive_enabled': True},
    "open-world app tools": {'apps."drive".open_world_enabled': True},
    "an enabled MCP server": {'mcp_servers."docs".enabled': True},
    "an MCP enabled-tools list": {'mcp_servers."docs".enabled_tools': ["search"]},
    "a prompting MCP tool": {'mcp_servers."docs".tools."search".approval_mode': "prompt"},
    "a prompting MCP default": {'mcp_servers."docs".default_tools_approval_mode': "prompt"},
    "an enabled plugin MCP server": {'plugins."kit".mcp_servers."docs".enabled': True},
    "a plugin MCP enabled-tools list": {'plugins."kit".mcp_servers."docs".enabled_tools': ["search"]},
    "a prompting plugin MCP tool": {'plugins."kit".mcp_servers."docs".tools."search".approval_mode': "prompt"},
    "a prompting plugin MCP default": {'plugins."kit".mcp_servers."docs".default_tools_approval_mode': "prompt"},
}
# The same keys where the inventory itself switches the app, server, plugin or tool off: `none` holds.
AGGREGATE_PRECONDITION_OFF = {
    "apps off": {**APP_ACTIVATION, "features.apps": False},
    "the app off": {**{key: value for key, value in APP_ACTIVATION.items() if key != "features.apps"},
                    'apps."drive".enabled': False},
    "the app's default tools off": {'apps."drive".enabled': True, 'apps."drive".default_tools_enabled': False,
                                    'apps."drive".tools."upload".approval_mode': "prompt"},
    "the app tool off": {'apps."drive".tools."upload".enabled': False,
                         'apps."drive".tools."upload".approval_mode': "auto"},
    "the MCP server off": {'mcp_servers."docs".enabled': False, 'mcp_servers."docs".enabled_tools': ["search"],
                           'mcp_servers."docs".tools."search".approval_mode': "prompt"},
    "an empty MCP enabled-tools list": {'mcp_servers."docs".enabled': True, 'mcp_servers."docs".enabled_tools': [],
                                        'mcp_servers."docs".tools."search".approval_mode': "prompt"},
    "the MCP tool disabled": {'mcp_servers."docs".disabled_tools': ["search"],
                              'mcp_servers."docs".tools."search".approval_mode': "prompt"},
    "plugins off": {"features.plugins": False, 'plugins."kit".mcp_servers."docs".enabled': True,
                    'plugins."kit".mcp_servers."docs".tools."search".approval_mode': "prompt"},
}


class ReadinessCodexPostureAggregateTest(ReadinessCase):
    """Cross-host review of d2db22fc8: reconcile the explicit inventory before trusting the aggregate controls."""

    default_host = "codex"
    request_id = "test-codex-posture-aggregate"

    def test_explicit_app_activation_cannot_hide_behind_a_none_aggregate(self) -> None:
        # `none` contradicts the four activations and both hints; `prompt` contradicts only the two hints.
        for aggregate, contradicted in (("none", 6), ("prompt", 2)):
            with self.subTest(aggregate=aggregate):
                probe = posture(controls={**CONTROLS, "app_tool_approval": aggregate},
                                settings={**SETTINGS, **APP_ACTIVATION})
                self.assert_item(self.item(probe), "unavailable", (
                    f"settings=0 outside, {contradicted} contradicted, 0 unobservable",), ("Keep current controls",))

    def test_dormant_app_settings_verify_when_apps_are_off(self) -> None:
        dormant = {**SETTINGS, **APP_ACTIVATION, "features.apps": False}
        self.assert_item(self.item(posture(controls={**CONTROLS, "app_tool_approval": "none"}, settings=dormant)),
                         "verified", ("controls=conservative", "settings=accounted"))
        self.assertEqual("verified", self.item(posture(controls={
            **CONTROLS, "app_tool_approval": "none", "app_destructive_tools": "enabled",
            "app_open_world_tools": "enabled"}, settings=dormant))["status"])

    def test_each_explicit_activation_contradicts_a_none_aggregate(self) -> None:
        assert_each(self, AGGREGATE_CONTRADICTIONS, "unavailable", ("settings=0 outside, 1 contradicted",), no_tools)

    def test_a_none_aggregate_holds_where_the_inventory_switches_its_precondition_off(self) -> None:
        assert_each(self, AGGREGATE_PRECONDITION_OFF, "verified", ("settings=accounted",), no_tools)

    def test_a_control_is_skipped_only_when_the_inventory_proves_its_precondition(self) -> None:
        hints = {**NO_TOOLS, "app_destructive_tools": "enabled", "app_open_world_tools": "unobservable"}
        self.assert_item(self.item(posture(controls=hints)), "unavailable", ("controls=1 outside, 1 unobservable",))
        self.assertEqual("unavailable", self.item(posture(controls=hints, settings={
            **SETTINGS, "features.apps": "unobservable"}))["status"])
        unproven = {key: value for key, value in SETTINGS.items() if key != "sandbox_mode"}
        writable = {**CONTROLS, "workspace_slash_tmp": "writable", "workspace_tmpdir": "unobservable"}
        self.assert_item(self.item(posture(sandbox_mode="read-only", controls=writable, settings=unproven)),
                         "unavailable", ("controls=1 outside, 1 unobservable",))
        self.assertEqual("verified", self.item(posture(sandbox_mode="read-only", controls=writable, settings={
            **unproven, "sandbox_mode": "read-only"}))["status"])


GRANULAR_CATEGORIES = ("sandbox_approval", "rules", "mcp_elicitations", "request_permissions", "skill_approval")


def auto_reviewed(policy: object) -> dict[str, object]:
    """`approvals_reviewer = auto_review` under `policy`, matching in the summary and the inventory."""
    inventory: dict[str, object] = {key: value for key, value in SETTINGS.items() if key != "approval_policy"}
    if isinstance(policy, dict):
        inventory.update({f"approval_policy.granular.{name}": flag for name, flag in policy["granular"].items()})
    else:
        inventory["approval_policy"] = policy
    return posture(approval_policy=policy, approvals_reviewer="auto_review",
                   settings={**inventory, "approvals_reviewer": "auto_review"})


class ReadinessCodexAutoReviewTest(ReadinessCase):
    """Daybreak F1263-a39e0934: automatic review is conservative only when no approval prompt can reach it."""

    default_host = "codex"
    request_id = "test-codex-auto-review"

    def test_auto_review_of_reachable_prompts_is_unavailable(self) -> None:
        for policy in ("on-request", "on-failure"):
            with self.subTest(policy=policy):
                self.assert_item(self.item(auto_reviewed(policy)), "unavailable",
                                 ("approvals_reviewer=auto_review", "settings=accounted"), ("Keep current controls",))
        for category in GRANULAR_CATEGORIES:
            granular = {name: name == category for name in GRANULAR_CATEGORIES}
            with self.subTest(granular=category):
                self.assert_item(self.item(auto_reviewed({"granular": granular})), "unavailable",
                                 ("approvals_reviewer=auto_review", "settings=accounted"))

    def test_auto_review_verifies_when_no_prompt_reaches_the_reviewer(self) -> None:
        self.assert_item(self.item(auto_reviewed("never")), "verified", ("approvals_reviewer=auto_review",))
        silent = dict.fromkeys(GRANULAR_CATEGORIES, False)
        self.assertEqual("verified", self.item(auto_reviewed({"granular": silent}))["status"])
        self.assertEqual("unknown", self.item(auto_reviewed("unobservable"))["status"])


# Daybreak F1263-13e52d6c: the checker reads a key only under the path Codex supports for it. Each family of
# tool settings, as (its key prefix, the prompting approval mode that rules out a `none` aggregate, its tool).
FAMILIES = {
    "the apps default table": ('apps."_default"', 'apps."_default".default_tools_approval_mode', "upload"),
    "the bare apps default table": ("apps._default", "apps._default.default_tools_approval_mode", "upload"),
    "an app": ('apps."drive"', 'apps."drive".tools."upload".approval_mode', "upload"),
    "an MCP server": ('mcp_servers."docs"', 'mcp_servers."docs".tools."search".approval_mode', "search"),
    "a plugin MCP server": ('plugins."kit".mcp_servers."docs"',
                            'plugins."kit".mcp_servers."docs".tools."search".approval_mode', "search"),
}
# Every off switch the checker reads, as the leaf under a family prefix and its off value (`{tool}` is the
# family's tool name).
OFF_SWITCHES = {"enabled": False, "default_tools_enabled": False, 'tools."{tool}".enabled': False,
                "enabled_tools": [], "disabled_tools": ["{tool}"]}
# Where Codex reads each switch: the families whose keys it switches off. `apps._default.enabled` is supported
# but disables only apps with no `[apps.<id>]` table, so it switches off no key the inventory names.
SWITCHES_OFF = {"enabled": {"an app", "an MCP server", "a plugin MCP server"},
                "default_tools_enabled": {"an app"}, 'tools."{tool}".enabled': {"an app"},
                "enabled_tools": {"an MCP server", "a plugin MCP server"},
                "disabled_tools": {"an MCP server", "a plugin MCP server"}}
NAMES_NOTHING = {("the apps default table", "enabled"), ("the bare apps default table", "enabled")}
# Daybreak's High probe: the valid default activation beside the ignored false key, bare and quoted.
IGNORED_DEFAULT = {"apps._default.enabled": True, "apps._default.default_tools_enabled": False}
IGNORED_DEFAULT_QUOTED = {'apps."_default".enabled': True, 'apps."_default".default_tools_enabled': False}


class ReadinessCodexKeyTableTest(ReadinessCase):
    """Daybreak F1263-13e52d6c: a key switches something off only under the path Codex reads it from."""

    default_host = "codex"
    request_id = "test-codex-key-table"

    def test_an_ignored_default_tools_key_never_switches_app_tools_off(self) -> None:
        read_tool = {'apps."drive".tools."repos/list".approval_mode': "prompt"}
        hints = {"apps._default.destructive_enabled": True, "apps._default.open_world_enabled": True}
        for label, changes, contradicted in (
                ("bare _default", IGNORED_DEFAULT, 1), ("quoted _default", IGNORED_DEFAULT_QUOTED, 1),
                ("a connected read tool", {**IGNORED_DEFAULT, **read_tool}, 2),
                ("destructive and open-world tools", {**IGNORED_DEFAULT_QUOTED, **hints}, 3),
                ("the ignored key true", {**IGNORED_DEFAULT, "apps._default.default_tools_enabled": True}, 1)):
            with self.subTest(label):
                self.assert_item(self.item(no_tools(changes)), "unavailable",
                                 (f"settings=1 outside, {contradicted} contradicted, 0 unobservable",),
                                 ("Keep current controls",))
        unread = {**IGNORED_DEFAULT, "apps._default.default_tools_enabled": "unobservable"}
        self.assert_item(self.item(no_tools(unread)), "unavailable", ("settings=0 outside, 1 contradicted, 1 unobservable",))
        self.assertEqual("unknown", self.item(no_tools({"apps._default.default_tools_enabled": "unobservable"}))["status"])
        self.assertEqual("unavailable", self.item(no_tools({"apps._default.default_tools_enabled": False}))["status"])
        # Without the ignored key the activation alone is contradicted, so removing it never verifies either.
        self.assert_item(self.item(no_tools({"apps._default.enabled": True})), "unavailable",
                         ("settings=0 outside, 1 contradicted",))

    def test_supported_off_switches_still_switch_off(self) -> None:
        legitimate = {
            "apps off": {"apps._default.enabled": True, "features.apps": False,
                         'apps."drive".tools."repos/list".approval_mode': "prompt"},
            "the app's default tools off": {'apps."drive".enabled': True, 'apps."drive".default_tools_enabled': False,
                                            'apps."drive".tools."repos/list".approval_mode': "prompt"},
            "the apps default off": {"apps._default.enabled": False},
            "the quoted apps default off": {'apps."_default".enabled': False},
        }
        assert_each(self, legitimate, "verified", ("settings=accounted",), no_tools)

    def test_the_apps_default_switch_disables_only_apps_without_a_table(self) -> None:
        """Codex keeps an app with any `[apps.<id>]` key at its own `enabled`, default true."""
        for label, activation in (("the app's prompting tool", {'apps."drive".tools."upload".approval_mode': "prompt"}),
                                  ("the app's reviewer", {'apps."drive".approvals_reviewer': "user",
                                                          'apps."drive".default_tools_approval_mode': "prompt"}),
                                  ("the default approval mode", {"apps._default.default_tools_approval_mode": "prompt"}),
                                  ("the default hints", {"apps._default.destructive_enabled": True})):
            with self.subTest(label):
                self.assert_item(self.item(no_tools({"apps._default.enabled": False, **activation})), "unavailable",
                                 ("settings=0 outside, 1 contradicted",))

    def test_an_off_switch_under_an_unsupported_path_switches_nothing_off(self) -> None:
        for (family, (prefix, activation, tool)), (leaf, off) in itertools.product(FAMILIES.items(),
                                                                                 OFF_SWITCHES.items()):
            key = f"{prefix}.{leaf.format(tool=tool)}"
            value = [tool] if off == ["{tool}"] else off
            if family in SWITCHES_OFF[leaf]:
                expected = ("verified", "settings=accounted")
            elif (family, leaf) in NAMES_NOTHING:
                expected = ("unavailable", "settings=0 outside, 1 contradicted")
            else:
                expected = ("unavailable", "settings=1 outside, 1 contradicted")
                with self.subTest(key=key, alone=True):
                    self.assert_item(self.item(no_tools({key: value})), "unavailable", ("settings=1 outside",))
            with self.subTest(key=key):
                self.assert_item(self.item(no_tools({key: value, activation: "prompt"})), expected[0], (expected[1],))
        for key, activation in (("features.mcp_servers", 'mcp_servers."docs".enabled'),
                                ("apps.enabled", 'apps."drive".enabled'), ("tools.apps", 'apps."drive".enabled')):
            with self.subTest(key=key):
                self.assert_item(self.item(no_tools({key: False, activation: True})), "unavailable",
                                 ("settings=1 outside, 1 contradicted",))
        self.assertEqual("verified", self.item(no_tools({'"features"."apps"': False, 'apps."drive".enabled': True,
                                                         'apps."drive".default_tools_enabled': True}))["status"])

    def test_the_key_table_is_the_single_source_of_every_rule(self) -> None:
        from speckit_pro_runner.helpers import readiness_posture_settings as module
        rules = {"modeled": set(module.MODELED_SETTINGS), "conservative": set(module.CONSERVATIVE_SETTINGS),
                 "inert": {".".join(f'"{part}"' if "." in part else part for part in rule)
                           for rule in module.INERT_SETTINGS}}
        self.assertEqual(set(module.CODEX_KEYS), rules["modeled"] | rules["conservative"] | rules["inert"])
        self.assertEqual(sum(len(keys) for keys in rules.values()), len(module.CODEX_KEYS))
        for key, (kind, effect, cite) in module.CODEX_KEYS.items():
            with self.subTest(key=key):
                self.assertIn(key, rules[kind])
                self.assertTrue(effect and cite)
                self.assertIn("config-reference", cite)
                self.assertEqual(key.startswith("apps._default."), "_default" in module.pattern(key))
        for key in ("apps._default.default_tools_enabled", 'apps._default.tools."upload".enabled',
                    "apps._default.enabled_tools", 'mcp_servers."docs".default_tools_enabled'):
            with self.subTest(key=key):
                self.assertIsNone(module.rule_for(module.MODELED_PATTERNS, module.key_path(key)))
        self.assertFalse(module.matches(module.pattern("apps.*.enabled"), ("apps", "_default", "enabled")))
        self.assertTrue(module.matches(module.pattern("apps._default.enabled"), ("apps", "_default", "enabled")))
        self.assertTrue(module.matches(module.pattern("mcp_servers.*.enabled"), ("mcp_servers", "_default", "enabled")))
        self.assertTrue(module.matches(module.pattern("apps.*.tools.*.enabled"), ("apps", "drive", "tools", "_default", "enabled")))
        settings = module.canonical_settings({"apps._default.default_tools_enabled": False,
                                              'apps."drive".default_tools_enabled': False,
                                              'plugins."demo@openai-curated-remote".enabled': False,
                                              'plugins."kit@local".enabled': False,
                                              'plugins."kit@contrib".enabled': False, **GIT_MARKETPLACE})
        self.assertIsNone(module.read(settings, "apps.*.default_tools_enabled", "_default"))
        self.assertIs(False, module.read(settings, "apps.*.default_tools_enabled", "drive"))
        self.assertIsNone(module.read(settings, "plugins.*.enabled", "demo@openai-curated-remote"))
        self.assertIsNone(module.read(settings, "plugins.*.enabled", "kit@local"))
        self.assertIs(False, module.read(settings, "plugins.*.enabled", "kit@contrib"))
        self.assertIsNone(module.rule_for(module.CONSERVATIVE_PATTERNS, ("plugins", "kit@local", "enabled")))
        self.assertEqual("plugins.*.enabled", module.rule_for(module.CONSERVATIVE_PATTERNS,
                                                              ("plugins", "kit@contrib", "enabled"), settings))
        with self.assertRaises(LookupError):
            module.read(settings, "apps._default.default_tools_enabled")


# Cross-host reviews cr1263h and cr1263i: plugin-scope and hook-scope off switches, local versus remote plugin
# sources, and `_default` in every position. A plugin's local off value counts only for a marketplace the
# inventory configures; every other key is unproven: a remote family, an OpenAI-managed marketplace, a
# user-named marketplace the inventory does not configure, or a bare name.
UNPROVEN_PLUGINS = ("demo@openai-curated-remote", "demo@created-by-me-remote", "demo@workspace-directory",
                    "demo@workspace-shared-with-me", "demo@workspace-shared-with-me-private",
                    "demo@workspace-shared-with-me-unlisted", "demo@openai-curated", "demo@openai-api-curated",
                    "demo@openai-bundled", "demo@openai-bundled-alpha", "kit@contrib", "kit@local", "kit",
                    "kit@", "@contrib")
LOCAL_MARKETPLACE = {'marketplaces."local".source': "local-marketplace", 'marketplaces."local".source_type': "local"}


def plugin_server(plugin: str, **changes: object) -> dict[str, object]:
    """One plugin MCP server enabled with automatic approval, the surface a `none` aggregate denies."""
    prefix = f'plugins."{plugin}".mcp_servers."docs"'
    return {f"{prefix}.enabled": True, f"{prefix}.default_tools_approval_mode": "auto", **changes}


# Daybreak F1263-9c553342: bounds on untrusted text reaching the model are never inert.
CONTENT_LIMITS = ("project_doc_max_bytes", "tool_output_token_limit",
                  'mcp_servers."docs".tools."search".output_token_limit')
# Codex reserves `_default` as the apps default table only; everywhere else it is an ordinary name.
DEFAULT_ELSEWHERE = {
    "an MCP server": {'mcp_servers."_default".enabled': False,
                      'mcp_servers."_default".tools."search".approval_mode': "prompt"},
    "a bare MCP server": {"mcp_servers._default.enabled": False,
                          "mcp_servers._default.default_tools_approval_mode": "prompt"},
    "a denied MCP tool": {'mcp_servers."docs".disabled_tools': ["_default"],
                          'mcp_servers."docs".tools."_default".approval_mode': "prompt"},
    "an app tool": {'apps."drive".tools."_default".enabled': False,
                    'apps."drive".tools."_default".approval_mode': "prompt"},
    "a plugin": {'plugins."_default".mcp_servers."docs".enabled': False,
                 'plugins."_default".mcp_servers."docs".tools."search".approval_mode': "prompt"},
    "a plugin MCP server": {'plugins."kit".mcp_servers."_default".enabled': False,
                            'plugins."kit".mcp_servers."_default".tools."search".approval_mode': "prompt"},
    "a project": {'projects."_default".trust_level': "untrusted"},
    "an unselected permissions profile": {'permissions."_default".network.enabled': True},
    "an environment filter": {'shell_environment_policy.filters."_default"': "exclude"},
}


class ReadinessCodexPluginScopeTest(ReadinessCase):
    """Cross-host review cr1263h: each off switch holds only where Codex reads it."""

    default_host = "codex"
    request_id = "test-codex-plugin-scope"

    def test_a_local_off_value_counts_only_for_a_marketplace_the_inventory_configures(self) -> None:
        for plugin in UNPROVEN_PLUGINS:
            with self.subTest(plugin=plugin):
                probe = {f'plugins."{plugin}".enabled': False, **plugin_server(plugin)}
                self.assert_item(self.item(no_tools(probe)), "unavailable",
                                 ("settings=1 outside, 2 contradicted, 0 unobservable",), ("Keep current controls",))
                self.assert_item(self.item(no_tools({f'plugins."{plugin}".enabled': False})), "unavailable",
                                 ("settings=1 outside, 0 contradicted",))
                remote_off = {"features.remote_plugin": False, f'plugins."{plugin}".enabled': False,
                              **plugin_server(plugin)}
                self.assert_item(self.item(no_tools(remote_off)), "unavailable", ("settings=1 outside, 2 contradicted",))
        # A configured marketplace proves the plugin local, so its off value switches the server off; the
        # marketplace keys themselves select external content and keep the posture from verifying.
        for plugin, marketplace in (("kit@contrib", GIT_MARKETPLACE), ("kit@local", LOCAL_MARKETPLACE)):
            with self.subTest(plugin=plugin):
                probe = {**marketplace, f'plugins."{plugin}".enabled': False, **plugin_server(plugin)}
                self.assert_item(self.item(no_tools(probe)), "unavailable",
                                 (f"settings={len(marketplace)} outside, 0 contradicted",))
                unread = {**dict.fromkeys(marketplace, "unobservable"), f'plugins."{plugin}".enabled': False,
                          **plugin_server(plugin)}
                self.assert_item(self.item(no_tools(unread)), "unavailable",
                                 (f"settings=1 outside, 2 contradicted, {len(marketplace)} unobservable",))
        # A marketplace the inventory configures under another name proves nothing for this plugin.
        probe = {**GIT_MARKETPLACE, 'plugins."kit@local".enabled': False, **plugin_server("kit@local")}
        self.assert_item(self.item(no_tools(probe)), "unavailable", ("settings=5 outside, 2 contradicted",))

    def test_explicit_plugin_scope_off_switches_still_switch_off(self) -> None:
        plugin = "demo@openai-curated-remote"
        prefix = f'plugins."{plugin}".mcp_servers."docs"'
        off = {
            "the plugin MCP server off": plugin_server(plugin, **{f"{prefix}.enabled": False}),
            "an empty plugin enabled-tools list": {f"{prefix}.enabled_tools": [],
                                                   f"{prefix}.tools.\"search\".approval_mode": "auto"},
            "a denied plugin tool": {f"{prefix}.disabled_tools": ["search"],
                                     f"{prefix}.tools.\"search\".approval_mode": "auto"},
            "plugins off": {"features.plugins": False, **plugin_server(plugin)},
            "plugins off beside a local plugin": {"features.plugins": False, **plugin_server("kit@local")},
            "plugins off alone": {"features.plugins": False},
            "the remote catalog off alone": {"features.remote_plugin": False},
        }
        assert_each(self, off, "verified", ("settings=accounted",), no_tools)
        for key in ("features.plugins", "features.remote_plugin"):
            with self.subTest(key=key):
                self.assert_item(self.item(no_tools({key: True})), "unavailable", ("settings=1 outside",))
                self.assertEqual("unknown", self.item(no_tools({key: "unobservable"}))["status"])
        self.refuse_each([no_tools({"features.plugins": "off"})])

    def test_hook_scope_off_switches_are_judged_alone(self) -> None:
        self.assert_item(self.item(settings(**{"features.codex_hooks": False})), "verified", ("settings=accounted",))
        self.assertEqual("verified", self.item(settings(**{"features.codex_hooks": False, "features.hooks": False}))["status"])
        for case in ({"features.codex_hooks": True}, {"features.hooks": False, "features.codex_hooks": True},
                     {"features.hooks": True, "features.codex_hooks": False}):
            with self.subTest(case=case):
                self.assert_item(self.item(settings(**case)), "unavailable", ("settings=1 outside",))
        self.refuse_each([settings(**{"features.codex_hooks": "no"})])

    def test_default_is_reserved_only_as_an_app_id(self) -> None:
        assert_each(self, DEFAULT_ELSEWHERE, "verified", ("settings=accounted",), no_tools)
        for key in ("apps._default.default_tools_enabled", 'apps."_default".tools."upload".enabled'):
            with self.subTest(key=key):
                self.assert_item(self.item(no_tools({key: False})), "unavailable", ("settings=1 outside",))

    def test_content_limits_are_never_inert(self) -> None:
        """Daybreak F1263-9c553342: a larger bound on untrusted text is never accounted for."""
        for key in CONTENT_LIMITS:
            with self.subTest(key=key):
                self.assert_item(self.item(settings(**{key: 1000000})), "unavailable", ("settings=1 outside",))
                self.assertEqual("unknown", self.item(settings(**{key: "unobservable"}))["status"])
        for value in (0, 1, 1024, 32768):
            with self.subTest(project_doc_max_bytes=value):
                self.assertEqual("verified", self.item(settings(project_doc_max_bytes=value))["status"])
        self.assertEqual("unavailable", self.item(settings(project_doc_max_bytes=32769))["status"])
        # The model, not the configuration, sets the default output budgets, so no value is provably smaller.
        for key, value in ((CONTENT_LIMITS[1], 0), (CONTENT_LIMITS[1], 100), (CONTENT_LIMITS[2], 1)):
            with self.subTest(key=key, value=value):
                self.assertEqual("unavailable", self.item(settings(**{key: value}))["status"])

    def test_counts_take_whole_numbers_in_their_codex_range(self) -> None:
        """Cross-host review cr1263i: an unsigned byte or token count is a whole number; one budget is non-zero."""
        for key in CONTENT_LIMITS[:2]:
            self.refuse_each([settings(**{key: bad}) for bad in (1.5, -1, True, "32768", [1], 0.0)])
        self.refuse_each([settings(**{CONTENT_LIMITS[2]: bad}) for bad in (0, 1.5, -1, True, "8000")])
        self.refuse_each([settings(**{'mcp_servers."docs".startup_timeout_ms': bad}) for bad in (0, 1.5, True)])
        self.assertEqual("verified", self.item(settings(**{'mcp_servers."docs".startup_timeout_ms': 10000}))["status"])
        self.assertEqual("verified", self.item(settings(**{'mcp_servers."docs".startup_timeout_sec': 9.5}))["status"])


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    return unittest.TestSuite([loader.loadTestsFromTestCase(ReadinessCodexTrustTest),
                               loader.loadTestsFromTestCase(ReadinessCodexPostureControlsTest),
                               loader.loadTestsFromTestCase(ReadinessCodexPostureSettingsTest),
                               loader.loadTestsFromTestCase(ReadinessCodexPostureEvidenceTest),
                               loader.loadTestsFromTestCase(ReadinessCodexPostureAggregateTest),
                               loader.loadTestsFromTestCase(ReadinessCodexAutoReviewTest),
                               loader.loadTestsFromTestCase(ReadinessCodexKeyTableTest),
                               loader.loadTestsFromTestCase(ReadinessCodexPluginScopeTest)])


def main() -> int:
    return run_counted(build_suite(), label="test-readiness-codex-trust")


if __name__ == "__main__":
    raise SystemExit(main())
