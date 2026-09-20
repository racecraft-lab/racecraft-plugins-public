#!/usr/bin/env python3
"""Capability-bound author and preview broker regression tests."""

from __future__ import annotations

import hashlib
import json
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


class PreviewLauncherTests(unittest.TestCase):
    """The isolated Codex preview observer's invocation boundary."""

    def setUp(self) -> None:
        from speckit_pro_runner import preview_launcher

        self.launcher = preview_launcher
        self.plugin_root = ROOT / "speckit-pro"
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.runtime_root = Path(self.temp.name) / "runtime"
        self.runtime_root.mkdir()

    def command(self) -> list[str]:
        # The runtimes are stubbed the way the sweep launcher's own tests stub
        # them: this asserts the invocation this launcher builds, and CI runners
        # carry no Codex install.
        codex_runtime = Path(self.temp.name) / "runtimes" / "bin" / "codex"
        python_runtime = Path(self.temp.name) / "runtimes" / "bin" / "python3"
        with unittest.mock.patch.object(self.launcher, "codex_executable", return_value=codex_runtime), \
                unittest.mock.patch.object(self.launcher, "python_executable", return_value=python_runtime):
            return self.launcher.codex_preview_command(
                plugin_root=self.plugin_root, runtime_root=self.runtime_root, capability="cap-token"
            )

    def test_invocation_reaches_exactly_one_broker_tool(self) -> None:
        command = self.command()
        self.assertEqual(("submit_preview_verdict",), self.launcher.OBSERVER_TOOL_NAMES)
        self.assertIn('mcp_servers.author-broker.enabled_tools=["submit_preview_verdict"]', command)
        for forbidden in ("create_preview_session", "close_session", "write_formal_file", "create_formal_session"):
            self.assertNotIn(forbidden, " ".join(c for c in command if c.startswith("mcp_servers")))

    def test_invocation_disables_network_and_ambient_configuration(self) -> None:
        command = self.command()
        for flag in ("--ignore-user-config", "--ignore-rules", "--ephemeral", "--strict-config", "--skip-git-repo-check"):
            self.assertIn(flag, command)
        self.assertIn("permissions.author-broker-only.network.enabled=false", command)
        self.assertIn('web_search="disabled"', command)
        self.assertIn('default_permissions="author-broker-only"', command)

    def test_isolated_filesystem_excludes_the_repository(self) -> None:
        command = self.command()
        filesystem = next(c for c in command if c.startswith("permissions.author-broker-only.filesystem="))
        self.assertIn(str(self.runtime_root.resolve()), filesystem)
        self.assertNotIn(str(ROOT), filesystem)

    def test_capability_and_trusted_prompt_reach_the_observer(self) -> None:
        command = self.command()
        prompt = command[-1]
        self.assertIn("cap-token", prompt)
        self.assertIn("mcp__author-broker__submit_preview_verdict", prompt)
        self.assertIn("--output-schema", command)
        schema = json.loads(self.launcher.output_schema_path(self.plugin_root).read_text(encoding="utf-8"))
        self.assertEqual(["verified", "denied", "unavailable"], schema["properties"]["verdict"]["enum"])
        self.assertFalse(schema["additionalProperties"])

    def test_missing_capability_is_refused(self) -> None:
        codex_runtime = Path(self.temp.name) / "runtimes" / "bin" / "codex"
        with unittest.mock.patch.object(self.launcher, "codex_executable", return_value=codex_runtime):
            with self.assertRaises(self.launcher.LauncherViolation):
                self.launcher.codex_preview_command(
                    plugin_root=self.plugin_root, runtime_root=self.runtime_root, capability=""
                )

    def test_prompt_attestation_refuses_an_unavailable_layout(self) -> None:
        with self.assertRaises(self.launcher.LauncherViolation):
            self.launcher.codex_preview_prompt_resource(Path(self.temp.name))

    def test_observation_rejects_output_the_observer_must_not_produce(self) -> None:
        digest = "b" * 64
        self.assertEqual("unavailable", self.launcher.preview_observation({"verdict": "unavailable", "artifact_sha256": digest}, digest)["verdict"])
        for bad in (
            {"verdict": "unavailable", "artifact_sha256": digest, "page_title": "leaked"},
            {"verdict": "looks-fine", "artifact_sha256": digest},
            {"verdict": "verified", "artifact_sha256": "c" * 64},
            {"verdict": "verified"},
            "verified",
        ):
            with self.assertRaises(self.launcher.LauncherViolation):
                self.launcher.preview_observation(bad, digest)

    def test_broker_rejection_closes_as_blocked_rather_than_raising(self) -> None:
        from speckit_pro_runner.helpers.read_only import preview_isolation_session

        repo = Path(self.temp.name) / "repo"
        (repo / "artifacts").mkdir(parents=True)
        page = repo / "artifacts" / "page.html"
        page.write_text("<!doctype html><title>x</title>", encoding="utf-8")
        for inputs in (
            {"named_surface": "observe_codex", "artifact_path": "artifacts/page.html", "expected_sha256": "0" * 64},
            {"named_surface": "observe_codex", "artifact_path": "../escape.html", "expected_sha256": "0" * 64},
            {"named_surface": "observe_codex", "artifact_path": "artifacts/missing.html", "expected_sha256": "0" * 64},
        ):
            with self.subTest(artifact_path=inputs["artifact_path"]):
                result = preview_isolation_session(inputs, repo)
                self.assertEqual(3, result["exit_code"])
                self.assertEqual(
                    {"status": "blocked", "reason": "preview_boundary_unavailable"},
                    json.loads(result["stdout"]),
                )

    def test_redeeming_broker_is_told_the_session_root(self) -> None:
        from speckit_pro_runner import author_broker

        command = self.command()
        broker_env = next(c for c in command if c.startswith("mcp_servers.author-broker.env="))
        self.assertIn(author_broker.STATE_ROOT_VARIABLE, broker_env)
        self.assertIn(str(author_broker._state_root()), broker_env)

    def test_operation_is_registered_for_the_parent_to_invoke(self) -> None:
        from speckit_pro_runner.helpers.registry import HELPERS

        entry = HELPERS["preview-isolation-session"]
        self.assertEqual("preview-isolation-session", entry.operation)
        self.assertEqual("python_authoritative", entry.promotion_status)


if __name__ == "__main__":
    suite = unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromTestCase(AuthorBrokerTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(PreviewLauncherTests),
    ])
    raise SystemExit(run_counted(suite, label="test-author-broker"))
