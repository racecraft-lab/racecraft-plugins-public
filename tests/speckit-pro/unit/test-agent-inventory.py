#!/usr/bin/env python3
"""Regression tests for the authoritative cross-client agent inventory."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for import_root in (PLUGIN_ROOT, LIB_DIR):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from speckit_pro_runner.agent_inventory import (  # noqa: E402
    AGENT_INVENTORY,
    AgentInventoryError,
    CLAUDE_REQUIRED_AGENT_NAMES,
    CODEX_OPTIONAL_AGENT_NAMES,
    CODEX_REQUIRED_AGENT_NAMES,
    inventory_source_errors,
    load_agent_inventory,
)
from test_result import run_counted  # noqa: E402


class AgentInventoryTests(unittest.TestCase):
    def write_inventory(self, inventory: dict) -> Path:
        temporary = tempfile.TemporaryDirectory(prefix="agent-inventory-")
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "agent_inventory.json"
        path.write_text(json.dumps(inventory), encoding="utf-8")
        return path

    def test_canonical_inventory_has_expected_shared_and_exception_counts(self) -> None:
        categories = [role["category"] for role in AGENT_INVENTORY["roles"]]
        self.assertEqual(categories.count("shared"), 12)
        self.assertEqual(categories.count("sweep_security"), 2)
        self.assertEqual(categories.count("brokered_observer"), 1)
        self.assertEqual(categories.count("optional_helper"), 1)
        self.assertEqual(len(CLAUDE_REQUIRED_AGENT_NAMES), 15)
        self.assertEqual(len(CODEX_REQUIRED_AGENT_NAMES), 12)
        self.assertEqual(CODEX_OPTIONAL_AGENT_NAMES, ("autopilot-fast-helper",))
        self.assertEqual(inventory_source_errors(PLUGIN_ROOT, AGENT_INVENTORY), [])

    def test_duplicate_role_fails_closed(self) -> None:
        inventory = copy.deepcopy(AGENT_INVENTORY)
        inventory["roles"].append(copy.deepcopy(inventory["roles"][0]))
        with self.assertRaisesRegex(AgentInventoryError, "duplicate name"):
            load_agent_inventory(self.write_inventory(inventory))

    def test_unexplained_platform_exception_fails_closed(self) -> None:
        inventory = copy.deepcopy(AGENT_INVENTORY)
        sweep = next(role for role in inventory["roles"] if role["category"] == "sweep_security")
        sweep["exception_reason"] = ""
        with self.assertRaisesRegex(AgentInventoryError, "requires an exception_reason"):
            load_agent_inventory(self.write_inventory(inventory))

    def test_missing_and_unexpected_agent_sources_fail_validation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-inventory-sources-") as directory:
            plugin_root = Path(directory)
            (plugin_root / "agents").mkdir()
            (plugin_root / "codex-agents").mkdir()
            for role in AGENT_INVENTORY["roles"]:
                for platform in ("claude_code", "codex"):
                    source = role[platform]["source"]
                    if source is not None:
                        path = plugin_root / source
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text("fixture", encoding="utf-8")
            (plugin_root / "agents" / "phase-executor.md").unlink()
            (plugin_root / "codex-agents" / "unexpected.toml").write_text(
                'name = "unexpected"\n', encoding="utf-8"
            )

            errors = inventory_source_errors(plugin_root, AGENT_INVENTORY)

        self.assertTrue(any("missing agent sources" in error for error in errors), errors)
        self.assertTrue(any("unexpected agent sources" in error for error in errors), errors)
        self.assertTrue(any("must be a regular file" in error for error in errors), errors)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AgentInventoryTests)
    return run_counted(suite, label="test-agent-inventory")


if __name__ == "__main__":
    raise SystemExit(main())
