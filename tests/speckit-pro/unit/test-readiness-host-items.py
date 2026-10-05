#!/usr/bin/env python3
"""Readiness items for Claude Code and both hosts' hooks (ADR 0008): probe, scope, MCP state, hook trust."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
LIB_DIR = TEST_DIR.parent / "lib"
sys.path.insert(0, str(LIB_DIR))

from host_skill_views import host_skill_root  # noqa: E402
from runner_invocation import assert_runner_response, run_runner  # noqa: E402
from test_result import run_counted  # noqa: E402

CLAUDE_ONLY = ("permission_probe", "plugin_scope", "mcp_authentication")
HOOKS = [{"hook": "Stop", "defined": True, "trust": "trusted"},
         {"hook": "PreToolUse", "defined": True, "trust": "trusted"}]


def detail(item: str, key: str, value: object, **extra: object) -> dict[str, object]:
    return {"item": item, "evidence_source": f"{item} observation", key: value, **extra}


def request(observations: list[dict[str, object]], host: str = "claude") -> dict[str, object]:
    body = {"host": host, "execution_mode": "interactive", "plugin_revision": "2.40.0",
            "observations": observations}
    return {"schema_version": "1.0", "request_id": "test-host-items", "helper_id": "write-readiness-record",
            "operation": "write-readiness-record", "mode": "apply", "inputs": body}


def scaffold_step(host: str) -> str:
    path = host_skill_root(host) / "speckit-scaffold-spec" / "SKILL.md"
    return path.read_text(encoding="utf-8").split("### 6.5 Write the Readiness Record", 1)[1].split("\n### ", 1)[0]


class ReadinessHostItemsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.root.joinpath(".specify").mkdir()

    def run_helper(self, observations: list[dict[str, object]], host: str = "claude") -> dict:
        _, response, _ = run_runner(request(observations, host), cwd=self.root)
        return response

    def items(self, response: dict) -> dict:
        assert_runner_response(self, response, "ok", 0)
        return response["data"]["record"]["items"]

    def test_denied_probe_prints_the_needed_allow_rules(self) -> None:
        probes = [{"probe": "runner_request", "outcome": "denied", "command": "python3"},
                  {"probe": "git_status", "outcome": "passed"}]
        response = self.run_helper([detail("permission_probe", "probes", probes)])
        item = self.items(response)["permission_probe"]
        self.assertEqual("unavailable", item["status"])
        rules = response["data"]["allow_rules"]
        self.assertEqual(["Bash(python3 -m speckit_pro_runner:*)", "Bash(printf:*)"], rules)
        for rule in rules:
            self.assertIn(rule, item["action"])
        self.assertNotIn("git status", item["action"])

    def test_denied_git_probe_names_only_the_git_rule_and_a_clean_probe_needs_none(self) -> None:
        git_denied = [{"probe": "runner_request", "outcome": "passed", "command": "python3"},
                      {"probe": "git_status", "outcome": "denied"}]
        response = self.run_helper([detail("permission_probe", "probes", git_denied)])
        self.items(response)
        self.assertEqual(["Bash(git status:*)"], response["data"]["allow_rules"])
        clean = [{**probe, "outcome": "passed"} for probe in git_denied]
        response = self.run_helper([detail("permission_probe", "probes", clean)])
        self.assertEqual("verified", self.items(response)["permission_probe"]["status"])
        self.assertEqual([], response["data"]["allow_rules"])

    def test_stale_worktree_scope_is_unavailable_with_the_fix(self) -> None:
        scope = {"scope": "project", "loaded_version": "2.39.0", "expected_version": "2.40.0"}
        item = self.items(self.run_helper([detail("plugin_scope", "scope", scope)]))["plugin_scope"]
        self.assertEqual("unavailable", item["status"])
        self.assertIn("claude plugin update speckit-pro --scope project", item["action"])
        self.assertIn("/reload-plugins", item["action"])
        current = {**scope, "loaded_version": "2.40.0"}
        item = self.items(self.run_helper([detail("plugin_scope", "scope", current)]))["plugin_scope"]
        self.assertEqual("verified", item["status"])
        unobserved = {"scope": "project", "expected_version": "2.40.0"}
        item = self.items(self.run_helper([detail("plugin_scope", "scope", unobserved)]))["plugin_scope"]
        self.assertEqual("unknown", item["status"])
        self.assertTrue(item["action"])

    def test_mcp_authentication_and_approval_states_name_the_user_action(self) -> None:
        servers = [{"server": "alpha", "state": "connected"},
                   {"server": "beta", "state": "needs_authentication"},
                   {"server": "gamma", "state": "pending_approval"}]
        item = self.items(self.run_helper([detail("mcp_authentication", "servers", servers)]))["mcp_authentication"]
        self.assertEqual("unavailable", item["status"])
        self.assertIn("claude mcp login beta", item["action"])
        self.assertIn("gamma", item["action"])
        self.assertIn("alpha=connected", item["evidence_source"])
        ok = self.items(self.run_helper([detail("mcp_authentication", "servers", servers[:1])]))
        self.assertEqual("verified", ok["mcp_authentication"]["status"])
        odd = [{"server": "delta", "state": "mystery"}]
        assert_runner_response(self, self.run_helper([detail("mcp_authentication", "servers", odd)]),
                               "input_error", 2)
        unobserved = [{"server": "delta", "state": "unknown"}]
        self.assertEqual("unknown", self.items(self.run_helper(
            [detail("mcp_authentication", "servers", unobserved)]))["mcp_authentication"]["status"])

    def test_hook_definitions_and_trust_state_are_recorded_on_both_hosts(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                items = self.items(self.run_helper([detail("hooks", "hooks", HOOKS)], host))
                self.assertEqual("verified", items["hooks"]["status"])
                self.assertIn("Stop=trusted", items["hooks"]["evidence_source"])
                self.assertIn("PreToolUse=trusted", items["hooks"]["evidence_source"])
                self.assertTrue(items["hooks"]["fingerprints"])
                untrusted = [{"hook": "Stop", "defined": True, "trust": "untrusted"}]
                item = self.items(self.run_helper([detail("hooks", "hooks", untrusted)], host))["hooks"]
                self.assertEqual("unavailable", item["status"])
                self.assertIn("/hooks", item["action"])
                missing = [{"hook": "Stop", "defined": False, "trust": "unobservable"}]
                item = self.items(self.run_helper([detail("hooks", "hooks", missing)], host))["hooks"]
                self.assertEqual("unavailable", item["status"])
                unobservable = [{"hook": "Stop", "defined": True, "trust": "unobservable"}]
                item = self.items(self.run_helper([detail("hooks", "hooks", unobservable)], host))["hooks"]
                self.assertEqual("unknown", item["status"])

    def test_codex_records_claude_only_items_as_not_applicable(self) -> None:
        items = self.items(self.run_helper([], "codex"))
        for name in CLAUDE_ONLY:
            self.assertEqual("not_applicable", items[name]["status"], name)
            self.assertNotIn("action", items[name])
        claude = self.items(self.run_helper([], "claude"))
        for name in (*CLAUDE_ONLY, "hooks"):
            self.assertEqual("unknown", claude[name]["status"], name)
            self.assertTrue(claude[name]["action"])
        self.assertEqual("unknown", items["hooks"]["status"])

    def test_malformed_host_item_observations_are_refused(self) -> None:
        cases = {
            "codex sends a claude-only item": ("codex", detail("plugin_scope", "scope", {})),
            "caller status on a derived item": ("claude", detail("hooks", "hooks", HOOKS, status="verified")),
            "unknown outcome": ("claude", detail("permission_probe", "probes",
                                                 [{"probe": "git_status", "outcome": "maybe"}])),
            "unknown probe": ("claude", detail("permission_probe", "probes",
                                               [{"probe": "rm", "outcome": "denied"}])),
            "absolute scope version": ("claude", detail("plugin_scope", "scope", {
                "scope": "project", "loaded_version": "/" + "tmp/x", "expected_version": "2.40.0"})),
            "bad scope": ("claude", detail("plugin_scope", "scope", {
                "scope": "managed", "loaded_version": "1", "expected_version": "2"})),
            "bad hook name": ("claude", detail("hooks", "hooks", [{"hook": "a b", "defined": True,
                                                                   "trust": "trusted"}])),
            "wrong detail key": ("claude", detail("hooks", "probes", [])),
        }
        for label, (host, observation) in cases.items():
            with self.subTest(label):
                assert_runner_response(self, self.run_helper([observation], host), "input_error", 2)
                self.assertFalse((self.root / ".specify" / "readiness").exists())

    def test_absolute_interpreter_is_printed_but_never_recorded(self) -> None:
        interpreter = "/" + "opt/tools/python3"
        probes = [{"probe": "runner_request", "outcome": "denied", "command": interpreter}]
        response = self.run_helper([detail("permission_probe", "probes", probes)])
        item = self.items(response)["permission_probe"]
        self.assertIn(f"Bash({interpreter} -m speckit_pro_runner:*)", response["data"]["allow_rules"])
        self.assertNotIn(interpreter, json.dumps(response["data"]["record"]))
        self.assertIn("<interpreter>", item["action"])

    def test_hostile_interpreter_text_never_reaches_an_allow_rule(self) -> None:
        hostile = ["/" + "opt/py*", "/" + "opt/py)", "python3)", "python3, Bash(*)", "Bash(*)", "py\nBash(*)",
                   "/" + "opt/py\nBash(*)", "py'x", 'py"x', "py;rm", "/" + "opt/../py", "py$(x)", "py*", ""]
        for command in hostile:
            with self.subTest(command=command):
                probes = [{"probe": "runner_request", "outcome": "denied", "command": command}]
                response = self.run_helper([detail("permission_probe", "probes", probes)])
                assert_runner_response(self, response, "input_error", 2)
                self.assertNotIn("allow_rules", response.get("data", {}))
                self.assertFalse((self.root / ".specify" / "readiness").exists())

    def test_every_printed_rule_comes_from_a_fixed_template(self) -> None:
        probes = [{"probe": "runner_request", "outcome": "denied", "command": "/" + "opt/tools/python3.12"},
                  {"probe": "git_status", "outcome": "prompted"}]
        rules = self.run_helper([detail("permission_probe", "probes", probes)])["data"]["allow_rules"]
        for rule in rules:
            self.assertRegex(rule, r"^Bash\((?:/?[A-Za-z0-9_./+-]+ -m speckit_pro_runner:\*|printf:\*|git status:\*)\)$")
        self.assertEqual(3, len(rules))

    def test_scaffold_documents_the_host_items_on_each_host(self) -> None:
        steps = {host: scaffold_step(host) for host in ("claude", "codex")}
        for host, step in steps.items():
            rows = {name: f"| `{name}` |" in step for name in (*CLAUDE_ONLY, "hooks")}
            self.assertEqual({"permission_probe": host == "claude", "plugin_scope": host == "claude",
                              "mcp_authentication": host == "claude", "hooks": True}, rows, host)
        self.assertIn("allow_rules", steps["claude"])
        self.assertIn("Claude Code only", steps["codex"])
        self.assertIn("`not_applicable`", steps["codex"])


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ReadinessHostItemsTest)


def main() -> int:
    return run_counted(build_suite(), label="test-readiness-host-items")


if __name__ == "__main__":
    raise SystemExit(main())
