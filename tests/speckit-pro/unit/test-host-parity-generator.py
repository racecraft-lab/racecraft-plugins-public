#!/usr/bin/env python3
"""Unit tests for the host-parity generator core: host blocks, derived Codex
enforcement, and the pairing manifest."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for import_root in (PLUGIN_ROOT, LIB_DIR):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from speckit_pro_runner.agent_inventory import AGENT_INVENTORY  # noqa: E402
from speckit_pro_runner.host_parity import (  # noqa: E402
    HostParityError,
    derive_codex_enforcement,
    emit_host,
    pairing_manifest,
    split_frontmatter,
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

    def test_balanced_blocks_keep_the_target_host_and_strip_the_other(self) -> None:
        text = SHARED + CODEX_BLOCK + CLAUDE_BLOCK + "Tail.\n"
        self.assertEqual(emit_host(text, "codex"), "Shared line.\nCodex only.\nTail.\n")
        self.assertEqual(emit_host(text, "claude"), "Shared line.\nClaude only.\nTail.\n")

    def test_text_without_markers_is_unchanged_for_both_hosts(self) -> None:
        text = "One.\n\nTwo.\n"
        self.assertEqual(emit_host(text, "codex"), text)
        self.assertEqual(emit_host(text, "claude"), text)

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


class FrontmatterTests(unittest.TestCase):
    def test_folded_description_does_not_leak_into_other_keys(self) -> None:
        fields, body = split_frontmatter(
            agent("name: a\ndescription: >\n  tools: not a key\n  more\ntools: Read, Grep\n")
        )
        self.assertEqual(fields["tools"], "Read, Grep")
        self.assertEqual(fields["name"], "a")
        self.assertEqual(body, "# Body\n")

    def test_missing_closing_fence_fails_closed(self) -> None:
        with self.assertRaisesRegex(HostParityError, "frontmatter"):
            split_frontmatter("---\nname: a\n# Body\n")

    def test_missing_opening_fence_fails_closed(self) -> None:
        with self.assertRaisesRegex(HostParityError, "frontmatter"):
            split_frontmatter("name: a\n---\n")


class EnforcementTests(unittest.TestCase):
    def assert_rejected(self, fields: dict[str, str], reason: str) -> None:
        with self.assertRaisesRegex(HostParityError, reason):
            derive_codex_enforcement(fields)

    def test_allowlist_without_mutation_tools_derives_read_only(self) -> None:
        derived = derive_codex_enforcement(
            {
                "tools": "Read, Grep, Glob, "
                "mcp__plugin_speckit-pro_research-broker__research_search, "
                "mcp__plugin_speckit-pro_research-broker__docs_query"
            }
        )
        self.assertEqual(derived.sandbox_mode, "read-only")
        self.assertEqual(
            derived.enabled_tools, {"research-broker": ("docs_query", "research_search")}
        )

    def test_allowlist_with_any_mutation_tool_derives_workspace_write(self) -> None:
        for tool in ("Write", "Edit", "MultiEdit"):
            with self.subTest(tool=tool):
                derived = derive_codex_enforcement({"tools": f"Read, {tool}"})
                self.assertEqual(derived.sandbox_mode, "workspace-write")
                self.assertEqual(derived.enabled_tools, {})

    def test_enabled_tools_group_per_broker_server(self) -> None:
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

    def test_allowlisted_foreign_mcp_tool_fails_closed(self) -> None:
        self.assert_rejected({"tools": "Read, mcp__tavily__search"}, "mcp__tavily__search")

    def test_no_allowlist_is_read_only_only_when_every_mutation_tool_is_denied(self) -> None:
        denied = derive_codex_enforcement(
            {"disallowedTools": "Write, Edit, MultiEdit, NotebookEdit, Skill"}
        )
        self.assertEqual(denied.sandbox_mode, "read-only")
        self.assertEqual(denied.enabled_tools, {})
        partial = derive_codex_enforcement({"disallowedTools": "Write, Skill"})
        self.assertEqual(partial.sandbox_mode, "workspace-write")
        self.assertEqual(derive_codex_enforcement({}).sandbox_mode, "workspace-write")

    def test_empty_allowlist_fails_closed(self) -> None:
        self.assert_rejected({"tools": " , "}, "empty")

    def test_config_keys_emit_sandbox_mode_but_no_unproven_enabled_tools_key(self) -> None:
        derived = derive_codex_enforcement(
            {"tools": "Read, mcp__plugin_speckit-pro_research-broker__docs_query"}
        )
        self.assertEqual(derived.config_keys(), {"sandbox_mode": "read-only"})

    def test_shipped_read_only_roles_derive_read_only(self) -> None:
        for name in ("clarify-executor", "codebase-analyst", "domain-researcher"):
            with self.subTest(role=name):
                fields, _ = split_frontmatter(
                    (PLUGIN_ROOT / "agents" / f"{name}.md").read_text(encoding="utf-8")
                )
                self.assertEqual(derive_codex_enforcement(fields).sandbox_mode, "read-only")


class PairingManifestTests(unittest.TestCase):
    def test_shared_roles_are_paired_with_both_sources(self) -> None:
        manifest = pairing_manifest(AGENT_INVENTORY)
        paired = manifest.paired
        self.assertEqual(len(paired), 12)
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


def main() -> int:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite(
        loader.loadTestsFromTestCase(case)
        for case in (HostBlockTests, FrontmatterTests, EnforcementTests, PairingManifestTests)
    )
    return run_counted(suite, label="test-host-parity-generator")


if __name__ == "__main__":
    raise SystemExit(main())
