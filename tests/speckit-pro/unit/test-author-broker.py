#!/usr/bin/env python3
"""Capability-bound author and preview broker regression tests."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
import sys

sys.path.insert(0, str(ROOT / "speckit-pro"))
sys.path.insert(0, str(ROOT / "tests/speckit-pro/lib"))

from speckit_pro_runner import author_broker
from test_result import run_counted


class AuthorBrokerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_temp = tempfile.TemporaryDirectory()
        self.state_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.repo_temp.cleanup)
        self.addCleanup(self.state_temp.cleanup)
        self.root = Path(self.repo_temp.name).resolve()
        self.state_root = Path(self.state_temp.name).resolve()
        patcher = unittest.mock.patch.object(author_broker, "_state_root", return_value=self.state_root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_formal_write_is_path_scoped_and_atomic(self) -> None:
        target = self.root / "formal/counter/Counter.tla"
        target.parent.mkdir(parents=True)
        session = author_broker.create_formal_session(
            repo_root=str(self.root),
            workflow_file="workflow.md",
            model_id="counter",
            permitted_paths=["formal/counter/Counter.tla"],
        )
        result = author_broker.write_formal_file(
            capability=session["capability"],
            target="formal/counter/Counter.tla",
            content="Init == TRUE\n",
        )
        self.assertEqual(result["target"], "formal/counter/Counter.tla")
        self.assertEqual(result["sha256"], hashlib.sha256(target.read_bytes()).hexdigest())
        self.assertEqual(target.read_text(), "Init == TRUE\n")
        author_broker.close_session(capability=session["capability"])

    def test_formal_write_rejects_off_list_target(self) -> None:
        target = self.root / "formal/counter/Counter.tla"
        target.parent.mkdir(parents=True)
        session = author_broker.create_formal_session(
            repo_root=str(self.root),
            workflow_file="workflow.md",
            model_id="counter",
            permitted_paths=["formal/counter/Counter.tla"],
        )
        with self.assertRaisesRegex(author_broker.BrokerViolation, "outside the permitted output list"):
            author_broker.write_formal_file(
                capability=session["capability"],
                target="formal/counter/Other.tla",
                content="Bad == TRUE\n",
            )
        self.assertFalse((self.root / "formal/counter/Other.tla").exists())
        author_broker.close_session(capability=session["capability"])

    def test_formal_write_rejects_symlink_escape(self) -> None:
        target = self.root / "formal/counter/Counter.tla"
        target.parent.mkdir(parents=True)
        target.write_text("safe\n")
        session = author_broker.create_formal_session(
            repo_root=str(self.root),
            workflow_file="workflow.md",
            model_id="counter",
            permitted_paths=["formal/counter/Counter.tla"],
        )
        outside = self.root / "outside.tla"
        outside.write_text("outside\n")
        target.unlink()
        target.symlink_to(outside)
        with self.assertRaisesRegex(author_broker.BrokerViolation, "symlink|escapes"):
            author_broker.write_formal_file(
                capability=session["capability"],
                target="formal/counter/Counter.tla",
                content="Bad == TRUE\n",
            )
        author_broker.close_session(capability=session["capability"])

    def test_formal_write_rejects_oversize_content(self) -> None:
        target = self.root / "formal/counter/Counter.tla"
        target.parent.mkdir(parents=True)
        session = author_broker.create_formal_session(
            repo_root=str(self.root),
            workflow_file="workflow.md",
            model_id="counter",
            permitted_paths=["formal/counter/Counter.tla"],
        )
        with self.assertRaisesRegex(author_broker.BrokerViolation, "exceeds the broker limit"):
            author_broker.write_formal_file(
                capability=session["capability"],
                target="formal/counter/Counter.tla",
                content="x" * (author_broker.MAX_CONTENT_BYTES + 1),
            )
        author_broker.close_session(capability=session["capability"])

    def test_preview_verdict_returns_only_closed_fields(self) -> None:
        artifact = self.root / "artifacts/plan.html"
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"<html><body>plan</body></html>\n")
        expected = hashlib.sha256(artifact.read_bytes()).hexdigest()
        session = author_broker.create_preview_session(
            repo_root=str(self.root),
            artifact_path="artifacts/plan.html",
            expected_sha256=expected,
        )
        result = author_broker.submit_preview_verdict(
            capability=session["capability"], verdict="verified"
        )
        self.assertEqual(set(result), {"verdict", "artifact_sha256"})
        self.assertEqual(result, {"verdict": "verified", "artifact_sha256": expected})
        author_broker.close_session(capability=session["capability"])

    def test_preview_verdict_rejects_drift(self) -> None:
        artifact = self.root / "artifacts/plan.html"
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"<html><body>plan</body></html>\n")
        expected = hashlib.sha256(artifact.read_bytes()).hexdigest()
        session = author_broker.create_preview_session(
            repo_root=str(self.root),
            artifact_path="artifacts/plan.html",
            expected_sha256=expected,
        )
        artifact.write_bytes(b"<html><body>changed</body></html>\n")
        with self.assertRaisesRegex(author_broker.BrokerViolation, "changed after session creation"):
            author_broker.submit_preview_verdict(
                capability=session["capability"], verdict="verified"
            )
        author_broker.close_session(capability=session["capability"])

    def test_capability_close_invalidates_later_use(self) -> None:
        artifact = self.root / "artifacts/plan.html"
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"<html><body>plan</body></html>\n")
        expected = hashlib.sha256(artifact.read_bytes()).hexdigest()
        session = author_broker.create_preview_session(
            repo_root=str(self.root),
            artifact_path="artifacts/plan.html",
            expected_sha256=expected,
        )
        author_broker.close_session(capability=session["capability"])
        with self.assertRaisesRegex(author_broker.BrokerViolation, "session is unavailable"):
            author_broker.submit_preview_verdict(
                capability=session["capability"], verdict="verified"
            )

    def test_closed_tool_manifest_and_dispatch(self) -> None:
        self.assertEqual(
            author_broker.TOOL_NAMES,
            (
                "create_formal_session",
                "write_formal_file",
                "create_preview_session",
                "submit_preview_verdict",
                "close_session",
            ),
        )
        with self.assertRaisesRegex(author_broker.BrokerViolation, "unknown author broker tool"):
            author_broker.call_tool("not-a-tool", {})

    def test_codex_reaches_the_author_broker_through_an_isolated_prompt_role(self) -> None:
        import json

        plugin_root = ROOT / "speckit-pro"
        codex_mcp = json.loads((plugin_root / ".codex-plugin/sweep-mcp.json").read_text(encoding="utf-8"))
        server = codex_mcp["mcpServers"]["author-broker"]
        self.assertEqual(["-m", "speckit_pro_runner.author_broker"], server["args"])
        self.assertEqual(".", server["cwd"])
        self.assertNotIn("env", server)
        self.assertEqual(
            codex_mcp,
            json.loads((ROOT / "dist/codex/speckit-pro/.codex-plugin/sweep-mcp.json").read_text(encoding="utf-8")),
        )

        self.assertFalse((plugin_root / "codex-agents/artifact-preview-observer.toml").exists())
        prompt = plugin_root / "codex-skills/speckit-autopilot/references/preview-prompts/observer.md"
        self.assertTrue(prompt.is_file())
        text = prompt.read_text(encoding="utf-8")
        self.assertIn("mcp__author-broker__submit_preview_verdict", text)
        self.assertNotIn("mcp__plugin_speckit-pro_author-broker__", text)
        for verdict in author_broker.PREVIEW_VERDICTS:
            self.assertIn(f"`{verdict}`", text)

    def test_inventory_records_the_observer_as_a_brokered_observer_role(self) -> None:
        from speckit_pro_runner.agent_inventory import AGENT_INVENTORY

        role = next(r for r in AGENT_INVENTORY["roles"] if r["name"] == "artifact-preview-observer")
        self.assertEqual("brokered_observer", role["category"])
        self.assertEqual(("plugin_agent", "required"), (role["claude_code"]["implementation"], role["claude_code"]["install_status"]))
        self.assertEqual(("isolated_prompt_role", "not_installed"), (role["codex"]["implementation"], role["codex"]["install_status"]))
        self.assertEqual(
            "codex-skills/speckit-autopilot/references/preview-prompts/observer.md",
            role["codex"]["source"],
        )


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(AuthorBrokerTests), label="test-author-broker"))
