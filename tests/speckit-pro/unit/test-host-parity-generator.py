#!/usr/bin/env python3
"""Unit tests for the host-parity generator core: host blocks, derived Codex
enforcement, and the pairing manifest."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for import_root in (PLUGIN_ROOT, LIB_DIR):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from speckit_pro_runner.agent_inventory import AGENT_INVENTORY  # noqa: E402
from speckit_pro_runner.codex_agent_generator import (  # noqa: E402
    generated_codex_files,
    render_codex_agent,
)
from speckit_pro_runner.host_parity import (  # noqa: E402
    CODEX_HOOK_POLICY_FILE,
    HostParityError,
    codex_hook_denial,
    load_codex_hook_policies,
    derive_codex_enforcement,
    derive_codex_hook_policy,
    emit_host,
    pairing_manifest,
    split_frontmatter,
    unexplained_blocks,
)
from test_result import run_counted  # noqa: E402


SHARED = "Shared line.\n"
CODEX_BLOCK = "<!-- host:codex -->\nCodex only.\n<!-- /host -->\n"
CLAUDE_BLOCK = "<!-- host:claude -->\nClaude only.\n<!-- /host -->\n"


def agent(frontmatter: str, body: str = "# Body\n") -> str:
    return f"---\n{frontmatter}---\n{body}"


class HostBlockTests(unittest.TestCase):
    def assert_rejected(self, text: str, reason: str, host: str = "codex") -> None:
        with self.assertRaisesRegex(HostParityError, reason):
            emit_host(text, host)

    # (source, Codex view, Claude view)
    VIEWS = (
        (SHARED + CODEX_BLOCK + CLAUDE_BLOCK + "Tail.\n",
         "Shared line.\nCodex only.\nTail.\n", "Shared line.\nClaude only.\nTail.\n"),
        ("One.\n\nTwo.\n", "One.\n\nTwo.\n", "One.\n\nTwo.\n"),
        ("<!-- host:codex: Codex runs exec_command -->\nCodex only.\n<!-- /host -->\n", "Codex only.\n", ""),
    )

    def test_each_host_keeps_its_own_blocks_and_no_marker_or_reason(self) -> None:
        views = [(emit_host(text, "codex"), emit_host(text, "claude")) for text, *_ in self.VIEWS]
        self.assertEqual(views, [(codex, claude) for _, codex, claude in self.VIEWS])

    def test_nested_block_fails_closed(self) -> None:
        self.assert_rejected(
            "<!-- host:codex -->\n<!-- host:claude -->\nx\n<!-- /host -->\n<!-- /host -->\n",
            "nested",
        )

    def test_unknown_host_fails_closed(self) -> None:
        self.assert_rejected("<!-- host:gemini -->\nx\n<!-- /host -->\n", "unknown host")

    def test_unknown_target_host_fails_closed(self) -> None:
        self.assert_rejected(SHARED, "unknown host", host="gemini")

    def test_unterminated_block_fails_closed(self) -> None:
        self.assert_rejected("<!-- host:codex -->\nx\n", "unterminated", host="claude")

    def test_close_without_open_fails_closed(self) -> None:
        self.assert_rejected("x\n<!-- /host -->\n", "without an open")

    def test_open_marker_with_trailing_text_fails_closed(self) -> None:
        self.assert_rejected("<!-- host:codex --> trailing\nx\n<!-- /host -->\n", "own line")

    def test_close_marker_after_text_fails_closed(self) -> None:
        self.assert_rejected("<!-- host:codex -->\nx <!-- /host -->\n", "own line")

    def test_open_marker_after_text_fails_closed(self) -> None:
        self.assert_rejected("lead <!-- host:claude -->\nx\n<!-- /host -->\n", "own line")

    def test_markers_inside_fenced_code_still_count(self) -> None:
        text = "```\n<!-- host:codex -->\nx\n<!-- /host -->\n```\n"
        self.assertEqual(emit_host(text, "claude"), "```\n```\n")

    def test_error_names_the_line_number(self) -> None:
        self.assert_rejected("ok\n<!-- /host -->\n", "line 2")

    def test_unexplained_blocks_lists_open_markers_without_a_reason(self) -> None:
        text = (
            "<!-- host:codex: why -->\nx\n<!-- /host -->\n"
            "<!-- host:claude -->\ny\n<!-- /host -->\n"
        )
        self.assertEqual(unexplained_blocks(text), [4])

    def test_a_blank_reason_fails_closed(self) -> None:
        self.assert_rejected("<!-- host:codex:   -->\nz\n<!-- /host -->\n", "line 1")


class FrontmatterTests(unittest.TestCase):
    def test_folded_description_does_not_leak_into_other_keys(self) -> None:
        fields, body = split_frontmatter(
            agent("name: a\ndescription: >\n  tools: not a key\n  more\ntools: Read, Grep\n")
        )
        self.assertEqual(fields["tools"], "Read, Grep")
        self.assertEqual(fields["name"], "a")
        self.assertEqual(body, "# Body\n")

    def test_folded_value_is_joined_like_yaml_folds_it(self) -> None:
        fields, _ = split_frontmatter(agent("name: a\ndescription: >\n  First line\n  second line.\ntools: Read\n"))
        self.assertEqual(fields["description"], "First line second line.")

    def test_missing_closing_fence_fails_closed(self) -> None:
        with self.assertRaisesRegex(HostParityError, "frontmatter"):
            split_frontmatter("---\nname: a\n# Body\n")

    def test_missing_opening_fence_fails_closed(self) -> None:
        with self.assertRaisesRegex(HostParityError, "frontmatter"):
            split_frontmatter("name: a\n---\n")


RESEARCH_TOOLS = (
    "mcp__plugin_speckit-pro_research-broker__research_search, "
    "mcp__plugin_speckit-pro_research-broker__docs_query"
)


class SandboxDerivationTests(unittest.TestCase):
    CASES = (
        ({"tools": "Read, Grep, " + RESEARCH_TOOLS}, "read-only"),
        ({"tools": "Read, Write"}, "workspace-write"),
        ({"tools": "Read, Edit"}, "workspace-write"),
        ({"tools": "Read, MultiEdit"}, "workspace-write"),
        ({"disallowedTools": "Write, Edit, MultiEdit, NotebookEdit, Skill"}, "read-only"),
        ({"disallowedTools": "Write, Skill"}, "workspace-write"),
        ({}, "workspace-write"),
    )

    def test_sandbox_mode_follows_the_mutation_tools_left_to_the_role(self) -> None:
        derived = [derive_codex_enforcement(fields).sandbox_mode for fields, _ in self.CASES]
        self.assertEqual(derived, [expected for _, expected in self.CASES])

    def test_advisory_config_keys_carry_only_sandbox_mode(self) -> None:
        derived = derive_codex_enforcement({"tools": "Read, " + RESEARCH_TOOLS})
        self.assertEqual(derived.advisory_config_keys(), {"sandbox_mode": "read-only"})

    def test_shipped_read_only_roles_derive_read_only(self) -> None:
        for name in ("clarify-executor", "codebase-analyst", "domain-researcher"):
            with self.subTest(role=name):
                fields, _ = split_frontmatter(
                    (PLUGIN_ROOT / "agents" / f"{name}.md").read_text(encoding="utf-8")
                )
                self.assertEqual(derive_codex_enforcement(fields).sandbox_mode, "read-only")


class BrokerAllowlistTests(unittest.TestCase):
    def test_broker_tools_group_per_server(self) -> None:
        derived = derive_codex_enforcement(
            {
                "tools": "Read, mcp__plugin_speckit-pro_author-broker__write_formal_file, "
                "mcp__plugin_speckit-pro_research-broker__docs_query, "
                "mcp__plugin_speckit-pro_author-broker__close_session"
            }
        )
        self.assertEqual(
            derived.enabled_tools,
            {
                "author-broker": ("close_session", "write_formal_file"),
                "research-broker": ("docs_query",),
            },
        )

    def test_roles_without_an_allowlist_have_no_broker_limit(self) -> None:
        self.assertIsNone(derive_codex_enforcement({"disallowedTools": "Write"}).enabled_tools)
        self.assertEqual(derive_codex_enforcement({"tools": "Read, Write"}).enabled_tools, {})

    def test_unmappable_allowlists_fail_closed(self) -> None:
        for fields, reason in (
            ({"tools": "Read, mcp__tavily__search"}, "mcp__tavily__search"),
            ({"tools": " , "}, "empty"),
        ):
            with self.subTest(fields=fields), self.assertRaisesRegex(HostParityError, reason):
                derive_codex_enforcement(fields)


READ_ONLY = {"disallowedTools": "Write, Edit, MultiEdit"}
DOCS_ONLY = {"tools": "Read, mcp__plugin_speckit-pro_research-broker__docs_query"}
OPEN_ROLE = {"disallowedTools": "Skill"}


class HookPolicyTests(unittest.TestCase):
    # (role fields, calling agent_type, tool name, denied?)
    DECISIONS = (
        (READ_ONLY, "probe-role", "apply_patch", True),
        (READ_ONLY, None, "apply_patch", False),
        (READ_ONLY, "other-role", "apply_patch", False),
        (READ_ONLY, "probe-role", "Bash", False),
        (DOCS_ONLY, "probe-role", "mcp__research_broker__docs_query", False),
        (DOCS_ONLY, "probe-role", "mcp__research_broker__research_search", True),
        (DOCS_ONLY, "probe-role", "mcp__codex_apps__tavily_tavily_research", True),
        (DOCS_ONLY, None, "mcp__research_broker__research_search", False),
        (OPEN_ROLE, "probe-role", "mcp__research_broker__research_search", False),
        (OPEN_ROLE, "probe-role", "apply_patch", False),
    )

    def test_policy_denies_only_the_role_and_tools_it_limits(self) -> None:
        decisions = [
            derive_codex_hook_policy("probe-role", derive_codex_enforcement(fields)).denies(
                agent_type, tool
            )
            for fields, agent_type, tool, _ in self.DECISIONS
        ]
        self.assertEqual(decisions, [denied for *_, denied in self.DECISIONS])

    def test_allowlist_names_use_the_codex_tool_spelling(self) -> None:
        allowed = derive_codex_hook_policy("r", derive_codex_enforcement(DOCS_ONLY)).allowed_mcp_tools
        self.assertEqual(allowed, ("mcp__research_broker__docs_query",))
        self.assertIsNone(
            derive_codex_hook_policy("r", derive_codex_enforcement(OPEN_ROLE)).allowed_mcp_tools
        )


class PairingManifestTests(unittest.TestCase):
    def test_shared_roles_are_paired_with_both_sources(self) -> None:
        manifest = pairing_manifest(AGENT_INVENTORY)
        paired = manifest.paired
        shared = {role["name"] for role in AGENT_INVENTORY["roles"] if role["category"] == "shared"}
        self.assertEqual(set(paired), shared)
        self.assertEqual(
            paired["domain-researcher"].claude_source, "agents/domain-researcher.md"
        )
        self.assertEqual(
            paired["domain-researcher"].codex_source, "codex-agents/domain-researcher.toml"
        )

    def test_single_host_roles_stay_on_their_own_host(self) -> None:
        manifest = pairing_manifest(AGENT_INVENTORY)
        self.assertEqual(manifest.codex_only, ("autopilot-fast-helper",))
        self.assertEqual(
            manifest.claude_only,
            ("artifact-preview-observer", "sweep-analyst", "sweep-classifier"),
        )
        self.assertTrue(set(manifest.paired).isdisjoint(manifest.claude_only + manifest.codex_only))

    def test_unrecognized_role_shape_fails_closed(self) -> None:
        inventory = copy.deepcopy(AGENT_INVENTORY)
        inventory["roles"][0]["codex"]["implementation"] = "none"
        with self.assertRaisesRegex(HostParityError, "phase-executor"):
            pairing_manifest(inventory)


CODEX_RECORD = {"model": "gpt-6-sol", "effort": "xhigh", "sandbox": "read-only"}
TRICKY_BODY = (
    "\n# Probe\n\nShared rule with a \\d regex and a \"\"\" fence.\n"
    "<!-- host:claude: Claude only -->\nClaude text.\n<!-- /host -->\n"
    "<!-- host:codex: Codex only -->\nCodex text ends in a quote\"\n<!-- /host -->\n"
)


def probe_agent(tools: str = "Read, Grep") -> str:
    return agent(f"name: probe\ndescription: >\n  Probe agent\n  for tests.\ntools: {tools}\n", TRICKY_BODY)


class CodexAgentGeneratorTests(unittest.TestCase):
    def test_rendered_file_parses_back_to_the_codex_view_of_the_source(self) -> None:
        text = render_codex_agent("probe", probe_agent(), CODEX_RECORD, "agents/probe.md")
        parsed = tomllib.loads(text)
        self.assertEqual(parsed["developer_instructions"], emit_host(TRICKY_BODY.lstrip("\n"), "codex"))
        self.assertNotIn("Claude text.", parsed["developer_instructions"])
        self.assertEqual(parsed["description"], "Probe agent for tests.")
        self.assertEqual(
            (parsed["name"], parsed["model"], parsed["model_reasoning_effort"], parsed["sandbox_mode"]),
            ("probe", "gpt-6-sol", "xhigh", "read-only"),
        )
        self.assertTrue(text.startswith("# Generated from agents/probe.md"))

    def test_inventory_sandbox_must_match_the_derived_sandbox(self) -> None:
        record = dict(CODEX_RECORD, sandbox="workspace-write")
        with self.assertRaisesRegex(HostParityError, "probe: inventory codex.sandbox"):
            render_codex_agent("probe", probe_agent(), record, "agents/probe.md")

    def test_a_name_mismatch_or_missing_description_fails_closed(self) -> None:
        with self.assertRaisesRegex(HostParityError, "is not 'other'"):
            render_codex_agent("other", probe_agent(), CODEX_RECORD, "agents/probe.md")
        with self.assertRaisesRegex(HostParityError, "no description"):
            render_codex_agent("probe", agent("name: probe\ntools: Read\n"), CODEX_RECORD, "agents/probe.md")

    def test_committed_codex_files_equal_their_generated_text(self) -> None:
        generated = generated_codex_files(PLUGIN_ROOT, AGENT_INVENTORY)
        self.assertEqual(
            set(generated),
            {role.codex_source for role in pairing_manifest(AGENT_INVENTORY).paired.values()}
            | {CODEX_HOOK_POLICY_FILE},
        )
        for relative, text in generated.items():
            with self.subTest(file=relative):
                self.assertEqual((PLUGIN_ROOT / relative).read_text(encoding="utf-8"), text)

    def test_every_host_block_in_a_paired_agent_states_its_reason(self) -> None:
        for role in pairing_manifest(AGENT_INVENTORY).paired.values():
            source = PLUGIN_ROOT / role.claude_source
            with self.subTest(agent=role.name):
                self.assertEqual(unexplained_blocks(source.read_text(encoding="utf-8")), [])


HOOK_SCRIPT = PLUGIN_ROOT / "scripts" / "codex-agent-policy-hook.py"


def run_hook(payload: object, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT), *(args or ("agent-policy-v1",))],
        input=payload if isinstance(payload, str) else json.dumps(payload),
        capture_output=True, text=True, check=False, timeout=60,
    )


class CodexAgentPolicyHookTests(unittest.TestCase):
    # (calling agent_type, tool name, denied?) against the shipped policy.
    CALLS = (
        ("domain-researcher", "mcp__sweep_broker__snapshot_list", True),
        ("domain-researcher", "mcp__research_broker__research_search", False),
        ("domain-researcher", "apply_patch", True),
        ("formal-model-author", "mcp__author_broker__write_formal_file", False),
        ("formal-model-author", "mcp__author_broker__create_formal_session", True),
        ("formal-model-author", "apply_patch", True),
        ("clarify-executor", "apply_patch", True),
        ("clarify-executor", "mcp__research_broker__docs_query", False),
        ("implement-executor", "apply_patch", False),
        (None, "apply_patch", False),
        (None, "mcp__sweep_broker__snapshot_list", False),
        ("some-other-agent", "apply_patch", False),
    )

    def test_the_shipped_hook_denies_only_what_each_role_policy_limits(self) -> None:
        decisions = []
        for agent_type, tool, _ in self.CALLS:
            payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {}}
            if agent_type:
                payload["agent_type"] = agent_type
            completed = run_hook(payload)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decisions.append(
                bool(completed.stdout.strip())
                and json.loads(completed.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
            )
        self.assertEqual(decisions, [denied for *_, denied in self.CALLS])

    def test_the_hook_fails_open_on_input_it_cannot_read(self) -> None:
        for payload in ("not json", "[1, 2]"):
            with self.subTest(payload=payload):
                completed = run_hook(payload)
                self.assertEqual((completed.returncode, completed.stdout), (0, ""))
                self.assertIn("no decision", completed.stderr)
        self.assertEqual(run_hook({}, "wrong-version").returncode, 2)

    def test_a_malformed_policy_fails_closed_in_the_loader(self) -> None:
        for text in ('{"schema_version": 2, "roles": {}}', '{"schema_version": 1, "roles": {"r": {"deny_file_edits": "yes"}}}',
                     '{"schema_version": 1, "roles": {"r": {"deny_file_edits": true, "allowed_mcp_tools": "all"}}}', "[]"):
            with self.subTest(text=text), self.assertRaises(HostParityError):
                load_codex_hook_policies(text)

    def test_the_parent_and_unlisted_agents_always_pass(self) -> None:
        policies = load_codex_hook_policies((PLUGIN_ROOT / CODEX_HOOK_POLICY_FILE).read_text(encoding="utf-8"))
        self.assertIsNone(codex_hook_denial({"tool_name": "apply_patch"}, policies))
        self.assertIsNone(codex_hook_denial({"agent_type": 7, "tool_name": "apply_patch"}, policies))


def main() -> int:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite(
        loader.loadTestsFromTestCase(case)
        for case in (
            HostBlockTests,
            FrontmatterTests,
            SandboxDerivationTests,
            BrokerAllowlistTests,
            HookPolicyTests,
            PairingManifestTests,
            CodexAgentGeneratorTests,
            CodexAgentPolicyHookTests,
        )
    )
    return run_counted(suite, label="test-host-parity-generator")


if __name__ == "__main__":
    raise SystemExit(main())
