#!/usr/bin/env python3
"""Deterministic contracts for the Layer 2 trigger runners."""

from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import tomllib
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LAYER2 = TESTS_ROOT / "layer2-trigger"
CLAUDE_RUNNER = LAYER2 / "run-trigger-evals.py"
CODEX_RUNNER = LAYER2 / "run-trigger-evals-codex.py"
CODEX_ENGINE = LAYER2 / "run_codex_evals.py"
SHARED_LIB = TESTS_ROOT / "lib"
_NO_SPECKIT_DESCRIPTION = (
    "Use when no available SpecKit skill covers the request, including ordinary coding, testing, tooling, or "
    "repository work and host-specific SpecKit operations whose matching skill is absent from the current catalog, "
    "such as installing Codex subagents when no agent-install skill is available or running the plan stage for an "
    "already-existing spec or populated workflow when no planning skill is available. Reply that no available "
    "SpecKit skill applies and stop."
)
_INSTALL_NEGATIVE = {
    "query": "install the bundled SpecKit Pro Codex subagents into ~/.codex/agents",
    "should_trigger": False,
}
_SCAFFOLD_NEGATIVES = [
    {
        "query": "SPEC-016 already has a committed workflow file with every prompt filled in, so resume it at the "
        "planning phase and run the plan stage against that existing file",
        "should_trigger": False,
    },
    {"query": "draft the implementation plan for SPEC-016; the spec already exists", "should_trigger": False},
]
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))

from test_result import run_counted  # noqa: E402


def import_script(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import script: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def assert_no_speckit_contracts(test: unittest.TestCase, claude: ModuleType, staged_text: str) -> None:
    engine = import_script(CODEX_ENGINE, "layer2_codex_no_speckit_contract")
    test.assertEqual(claude.NO_SPECKIT_SKILL_DESCRIPTION, _NO_SPECKIT_DESCRIPTION)
    test.assertEqual(engine.NO_SPECKIT_SKILL_DESCRIPTION, _NO_SPECKIT_DESCRIPTION)
    test.assertTrue(staged_text.startswith(f"---\nname: no-speckit-skill\ndescription: {_NO_SPECKIT_DESCRIPTION}\n---\n"))
    for eval_dir in ("evals", "codex-evals"):
        with test.subTest(eval_dir=eval_dir):
            install_cases = json.loads((LAYER2 / eval_dir / "speckit-install-trigger.json").read_text())
            scaffold_cases = json.loads((LAYER2 / eval_dir / "speckit-scaffold-spec-trigger.json").read_text())
            test.assertEqual(install_cases[12], _INSTALL_NEGATIVE)
            test.assertEqual(scaffold_cases[18:20], _SCAFFOLD_NEGATIVES)


def calls_forbidden_process_api(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "system":
                return True
            if any(
                keyword.arg == "shell"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in node.keywords
            ):
                return True
    return False


def has_hardcoded_python3_command(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return any(
        isinstance(node, (ast.List, ast.Tuple))
        and any(isinstance(item, ast.Constant) and item.value == "python3" for item in node.elts)
        for node in ast.walk(tree)
    )


def claude_stream(
    plugin_root: Path,
    plugin_name: str,
    expected_skill: str,
    nonce: str,
    *,
    selected: bool = True,
    model: str | None = "claude-sonnet-test",
) -> bytes:
    init: dict[str, object] = {
        "type": "system",
        "subtype": "init",
        "plugins": [{"name": plugin_name, "path": str(plugin_root)}],
        "plugin_errors": [],
        "mcp_servers": [],
        "mcp_server_errors": [],
        "tools": ["Skill"],
        "skills": [expected_skill, f"{plugin_name}:no-speckit-skill"],
    }
    if model is not None:
        init["model"] = model
    events: list[dict[str, object]] = [init]
    if selected:
        events.extend(
            [
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Skill",
                                "id": "toolu-skill",
                                "input": {"skill": expected_skill},
                            }
                        ]
                    },
                },
                {
                    "type": "user",
                    "message": {
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": "toolu-skill",
                                "is_error": False,
                                "content": "loaded",
                            }
                        ]
                    },
                },
            ]
        )
    events.extend(
        [
            {
                "type": "assistant",
                "message": {"content": [{
                    "type": "text",
                    "text": nonce if selected else "No skill selected.",
                }]},
            },
            {"type": "result", "subtype": "success", "is_error": False, "model": "untrusted-result-model"},
        ]
    )
    return ("\r\n".join(json.dumps(event) for event in events) + "\r\n").encode("utf-8")


def codex_witness(skill_name: str, marker: str) -> dict[str, dict[str, str]]:
    path = Path("/tmp/layer2-codex-fixture") / skill_name / "SKILL.md"
    body = f"---\nname: {skill_name}\ndescription: Fixture.\n---\n\n{marker}\n"
    return {skill_name: {
        "marker": marker,
        "path": str(path),
        "relative_path": f".agents/skills/{skill_name}/SKILL.md",
        "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "body": body,
    }}


def codex_stream(
    witnesses: dict[str, dict[str, str]],
    *,
    selected_skill: str | None = None,
    consulted_skill: str | None = None,
    message: str | None = None,
) -> bytes:
    skill_read = selected_skill or consulted_skill
    events: list[dict[str, object]] = [
        {"type": "thread.started", "thread_id": "thread-1"},
        {"type": "turn.started"},
    ]
    if skill_read is not None:
        witness = witnesses[skill_read]
        command = f"cat {witness['path']}"
        item = {"id": f"read-{skill_read}", "type": "command_execution", "command": command}
        events.append({"type": "item.started", "item": item})
        events.append({"type": "item.completed", "item": {
            **item,
            "status": "completed",
            "exit_code": 0,
            "aggregated_output": witness["body"],
        }})
    if message is None:
        message = witnesses[selected_skill]["marker"] if selected_skill is not None else "No skill selected."
    events.extend([
        {"type": "item.completed", "item": {"id": "message", "type": "agent_message", "text": message}},
        {"type": "turn.completed"},
    ])
    return ("\n".join(json.dumps(event) for event in events) + "\n").encode("utf-8")


def inspect_codex_events(
    engine: ModuleType,
    events: list[dict[str, object]],
    target_skill: str,
    witnesses: dict[str, dict[str, str]],
) -> dict[str, object]:
    payload = "\n".join(json.dumps(event) for event in events).encode("utf-8")
    return engine.inspect_codex_jsonl(
        payload, target_skill, witnesses,
    )


class FakePopen:
    def __init__(self, stdout: bytes, stderr: bytes = b"", returncode: int = 0) -> None:
        self.stdout_value = stdout
        self.stderr_value = stderr
        self.returncode = returncode
        self.pid = 43210
        self.communicate_calls = 0
        self.timeout = False

    def communicate(self, timeout: int | None = None) -> tuple[bytes, bytes]:
        self.communicate_calls += 1
        if self.timeout and self.communicate_calls == 1:
            raise subprocess.TimeoutExpired(
                ["claude"],
                timeout or 1,
                output=self.stdout_value,
                stderr=self.stderr_value,
            )
        return self.stdout_value, self.stderr_value

    def poll(self) -> int | None:
        return None if self.timeout and self.communicate_calls < 2 else self.returncode

    def terminate(self) -> None:
        self.returncode = -15

    def wait(self, timeout: int | None = None) -> int:
        return self.returncode


def successful_process_evidence(
    requested_model: str, *, host: str = "claude",
) -> dict[str, object]:
    """Explicit synthetic supervisor receipt; never used for provider execution."""
    return {
        "provider_exit_code": 0, "timed_out": False, "interrupted_by_signal": None,
        "cleanup_verified": True, "cleanup_error": None, "cleanup_scope": "owned-process-group",
        "unexpected_descendants": False, "child_pid": 43210, "child_pgid": 43210,
        "cleanup_observations": [{"pgid": 43210, "errno": 3, "elapsed_seconds": 0.01}],
        "process_error": None,
        "launch_contract": {
            "config_isolated": True,
            "retries_disabled": True,
            "requested_model": requested_model,
            **({"stdin_prompt_isolated": True} if host == "codex" else {}),
        },
    }


def supervised_results(results: list[tuple[int, bytes, bytes, bool]], requested_model: str):
    remaining = iter(results)

    def provider(*_args: object, **kwargs: object) -> tuple[int, bytes, bytes, bool]:
        result = next(remaining)
        kwargs["process_evidence"].update(successful_process_evidence(requested_model))
        return result

    return provider


class Layer2TriggerRunnerTests(unittest.TestCase):
    def test_preflight_keyboard_interrupt_preserves_runner_exit_and_cleanup(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                engine = import_script(CLAUDE_RUNNER if host == "claude" else CODEX_ENGINE, f"preflight_interrupt_{host}")
                source = root / "SKILL.md"
                source.write_text("---\nname: demo\ndescription: Demo.\n---\nBody.\n", encoding="utf-8")
                corpus = root / "corpus.json"
                corpus.write_text('[{"query":"q","should_trigger":false}]', encoding="utf-8")
                workspace, evidence = root / "workspace", root / "evidence"
                workspace.mkdir()
                argv = ["demo", "--evidence-dir", str(evidence)]
                with contextlib.ExitStack() as stack:
                    stack.enter_context(mock.patch.object(engine, "find_eval_file", return_value=corpus))
                    stack.enter_context(mock.patch.object(engine, "find_skill_source", return_value=source))
                    stack.enter_context(mock.patch.object(engine.shutil, "which", return_value=f"/stub/{host}"))
                    stack.enter_context(mock.patch.object(engine.tempfile, "mkdtemp", return_value=str(workspace)))
                    provider = stack.enter_context(mock.patch.object(engine, f"run_{host}_query"))
                    if host == "claude":
                        stack.enter_context(mock.patch.object(engine, "cli_preflight", side_effect=KeyboardInterrupt))
                    else:
                        stack.enter_context(mock.patch.object(engine.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b"", b"")))
                        stack.enter_context(mock.patch.object(engine, "enumerate_non_target_skills", return_value=()))
                        stack.enter_context(mock.patch.object(engine, "enumerate_mcp_servers", return_value=()))
                        stack.enter_context(mock.patch.object(engine, "offline_catalog_preflight", side_effect=KeyboardInterrupt))
                        stack.enter_context(mock.patch.object(sys, "argv", [str(CODEX_ENGINE), *argv]))
                    stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                    stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
                    code = engine.main(argv) if host == "claude" else engine.main()
                self.assertEqual(code, 130)
                self.assertFalse(workspace.exists())
                provider.assert_not_called()
                if host == "codex":
                    receipt = json.loads((evidence / "arm-cleanup.json").read_text())
                    self.assertEqual(receipt["runner_exit_code"], 130)
                    self.assertTrue(receipt["workspace_removed"])

    def test_main_retains_canonical_trial_before_next_launch_and_stops_invalid(self) -> None:
        for host in ("claude", "codex"):
            for scenario in ("good", "nonzero", "timeout", "missing-receipt", "interrupted", "cleanup-failed"):
                with self.subTest(host=host, scenario=scenario), tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    engine = import_script(CLAUDE_RUNNER if host == "claude" else CODEX_ENGINE, f"canonical_{host}_{scenario}")
                    source = root / "SKILL.md"
                    source.write_text("---\nname: demo\ndescription: Demo.\n---\nBody.\n", encoding="utf-8")
                    corpus = root / "corpus.json"
                    corpus.write_text(json.dumps([{"query": "first", "should_trigger": False},
                                                  {"query": "second", "should_trigger": False}]), encoding="utf-8")
                    workspace, evidence = root / "workspace", root / "evidence"
                    workspace.mkdir()
                    fixed_id = "123456789012"
                    plugin_name = f"skill-catalog-eval-{fixed_id}"
                    raw = claude_stream(workspace, plugin_name, f"{plugin_name}:demo-eval-{fixed_id}", "nonce", selected=False)
                    if host == "codex":
                        raw = "\n".join(map(json.dumps, [
                            {"type": "thread.started", "thread_id": "thread-1"}, {"type": "turn.started"},
                            {"type": "item.completed", "item": {"type": "agent_message", "text": "No skill needed."}},
                            {"type": "turn.completed"},
                        ])).encode()
                    calls = []

                    def provider(*_args: object, **kwargs: object) -> tuple[int, bytes, bytes, bool]:
                        if calls:
                            self.assertEqual(len(list(evidence.glob("*.trial.json"))), len(calls))
                        calls.append(True)
                        requested_model = "claude-sonnet-test" if host == "claude" else "gpt-5.6-sol"
                        receipt = successful_process_evidence(requested_model, host=host)
                        receipt.update(provider_exit_code=7 if scenario == "nonzero" else -15 if scenario == "timeout" else 0,
                                       timed_out=scenario == "timeout")
                        if scenario == "cleanup-failed":
                            receipt.update(cleanup_verified=False, cleanup_error="owned scope probe failed")
                        if scenario != "missing-receipt":
                            kwargs["process_evidence"].update(receipt)
                        if scenario == "interrupted":
                            error = engine.processes.TerminationRequested(signal.SIGTERM)
                            error.process_evidence = receipt
                            error.stdout, error.stderr = raw, b"stderr\xff"
                            raise error
                        return (-1 if scenario == "timeout" else receipt["provider_exit_code"], raw, b"stderr\xff", scenario == "timeout")

                    output = io.StringIO()
                    diagnostics = io.StringIO()
                    argv = ["demo", "--evidence-dir", str(evidence), "--model", "claude-sonnet-test" if host == "claude" else "gpt-5.6-sol"]
                    with contextlib.ExitStack() as stack:
                        for name, replacement in (
                            ("find_eval_file", corpus), ("find_skill_source", source),
                        ):
                            stack.enter_context(mock.patch.object(engine, name, return_value=replacement))
                        stack.enter_context(mock.patch.object(engine.shutil, "which", return_value=f"/stub/{host}"))
                        stack.enter_context(mock.patch.object(engine.tempfile, "mkdtemp", return_value=str(workspace)))
                        stack.enter_context(mock.patch.object(engine.uuid, "uuid4", return_value=SimpleNamespace(hex=fixed_id)))
                        stack.enter_context(mock.patch.object(engine, f"run_{host}_query", side_effect=provider))
                        if host == "claude":
                            stack.enter_context(mock.patch.object(engine, "cli_preflight", return_value=({}, "ok")))
                        else:
                            stack.enter_context(mock.patch.object(engine.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b"", b"")))
                            stack.enter_context(mock.patch.object(engine, "enumerate_non_target_skills", return_value=()))
                            stack.enter_context(mock.patch.object(engine, "enumerate_mcp_servers", return_value=()))
                            stack.enter_context(mock.patch.object(engine, "offline_catalog_preflight", return_value=({}, "ok")))
                            stack.enter_context(mock.patch.object(engine, "cli_preflight", return_value=({}, "ok")))
                            stack.enter_context(mock.patch.object(sys, "argv", [str(CODEX_ENGINE), *argv]))
                        stack.enter_context(contextlib.redirect_stdout(output))
                        stack.enter_context(contextlib.redirect_stderr(diagnostics))
                        code = engine.main(argv) if host == "claude" else engine.main()
                    self.assertEqual(code, 0 if scenario == "good" else 143 if scenario == "interrupted" else 1)
                    self.assertEqual(len(calls), 6 if scenario == "good" else 1)
                    report = json.loads(output.getvalue())
                    trial = report["results"][0]["selection_evidence"][0]
                    self.assertIs(trial["stream_valid"], True)
                    self.assertIs(trial["trial_valid"], scenario == "good")
                    self.assertIs(trial["valid"], trial["trial_valid"])
                    self.assertIs(
                        trial["qualification_eligible"],
                        scenario == "good" and host == "codex",
                    )
                    self.assertEqual(trial["provider_exit_code"], None if scenario == "missing-receipt" else 7 if scenario == "nonzero" else -15 if scenario == "timeout" else 0)
                    self.assertEqual(trial["exit_code"], trial["provider_exit_code"])
                    self.assertIs(report["summary"]["complete"], scenario == "good")
                    if scenario != "good":
                        self.assertEqual(report["results"][1]["status"], "not_run")
                        self.assertIsNone(report["results"][1]["selected" if host == "claude" else "triggers"])
                        self.assertIsNone(report["results"][0]["trigger_rate"])
                    receipt = json.loads((evidence / "arm-cleanup.json").read_text())
                    self.assertTrue(receipt["workspace_removed"])
                    self.assertEqual(receipt["runner_exit_code"], code)
                    self.assertFalse(workspace.exists())
                    if host == "codex":
                        self.assertIn("[ 1/2] expect=NOOP trig=", diagnostics.getvalue())

    @unittest.skipIf(os.name == "nt", "POSIX owned process-group contract")
    def test_codex_timeout_drains_inherited_pipes_and_removes_owned_descendant(self) -> None:
        engine = import_script(CODEX_ENGINE, "layer2_codex_inherited_pipes")
        original_popen = subprocess.Popen
        owned = []
        descendant = "import time; print('child ready', flush=True); time.sleep(30)"
        leader = (
            "import subprocess,sys\n"
            f"subprocess.Popen([sys.executable,'-u','-c',{descendant!r}])\n"
            "print('leader finished', flush=True)\n"
        )

        def launch(_command: object, **kwargs: object) -> subprocess.Popen:
            kwargs.pop("executable", None)
            child = original_popen([sys.executable, "-u", "-c", leader], **kwargs)
            owned.append(child)
            return child

        execution = {}
        with tempfile.TemporaryDirectory() as temporary:
            try:
                with mock.patch.object(engine, "codex_executable", return_value=sys.executable), mock.patch.object(
                    engine.subprocess, "Popen", side_effect=launch,
                ):
                    rc, stdout, _stderr, timed_out = engine.run_codex_query(
                        Path(temporary), "q", "low", "gpt-test", 1, [], process_evidence=execution,
                    )
                self.assertTrue(timed_out)
                self.assertEqual(rc, -1, "the legacy helper sentinel is not the observed provider exit")
                self.assertEqual(execution["provider_exit_code"], 0)
                self.assertTrue(execution["cleanup_verified"])
                self.assertEqual(execution["cleanup_observations"][-1]["errno"], 3)
                self.assertIn(b"child ready", stdout)
                self.assertIn(b"leader finished", stdout)
                with self.assertRaises(ProcessLookupError):
                    os.killpg(owned[0].pid, 0)
            finally:
                for child in owned:
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        # The runner already removed the owned process group.
                        pass
                    child.wait(timeout=5)

    @unittest.skipIf(os.name == "nt", "POSIX owned process-group contract")
    def test_codex_completed_leader_cannot_leave_an_owned_descendant(self) -> None:
        engine = import_script(CODEX_ENGINE, "layer2_codex_owned_descendant")
        original_popen = subprocess.Popen
        owned = []
        descendant = "import time; print('ready', flush=True); time.sleep(30)"
        leader = (
            "import subprocess,sys\n"
            f"child=subprocess.Popen([sys.executable,'-u','-c',{descendant!r}], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)\n"
            "assert child.stdout.readline() == b'ready\\n'\n"
            "child.stdout.close()\n"
            "print('leader finished', flush=True)\n"
        )

        def launch(_command: object, **kwargs: object) -> subprocess.Popen:
            kwargs.pop("executable", None)
            kwargs["start_new_session"] = True
            child = original_popen([sys.executable, "-u", "-c", leader], **kwargs)
            owned.append(child)
            return child

        with tempfile.TemporaryDirectory() as temporary:
            try:
                with mock.patch.object(engine, "codex_executable", return_value=sys.executable), mock.patch.object(
                    engine.subprocess, "Popen", side_effect=launch,
                ):
                    with self.assertRaises(OSError):
                        engine.run_codex_query(Path(temporary), "q", "low", "gpt-test", 5, [])
                with self.assertRaises(ProcessLookupError):
                    os.killpg(owned[0].pid, 0)
            finally:
                for child in owned:
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        # The runner already removed the owned process group.
                        pass
                    child.wait(timeout=5)

    def test_claude_rejects_invalid_sibling_completion_and_observed_contract_conflicts(self) -> None:
        claude = import_script(CLAUDE_RUNNER, "layer2_claude_evidence_contract")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plugin, target, nonce = "catalog", "catalog:demo", "target-nonce"
            original = [json.loads(line) for line in claude_stream(root, plugin, target, nonce).splitlines()]
            scenarios = {}
            for label in ("errored", "missing", "before-init", "duplicate-result", "orphan-result"):
                events = json.loads(json.dumps(original))
                events[1]["message"]["content"][0]["input"]["skill"] = "catalog:no-speckit-skill"
                if label == "errored":
                    events[2]["message"]["content"][0]["is_error"] = True
                elif label == "missing":
                    del events[2]
                elif label == "before-init":
                    events[0], events[1] = events[1], events[0]
                elif label == "duplicate-result":
                    events.insert(3, events[2])
                else:
                    events[2]["message"]["content"][0]["tool_use_id"] = "unknown"
                scenarios[label] = events
            events = json.loads(json.dumps(original))
            events[1]["message"]["content"][0].update(name="Bash", input={"command": "true"})
            scenarios["undeclared-tool"] = events
            events = json.loads(json.dumps(original))
            events[0]["model"] = "claude-opus-test"
            scenarios["wrong-init-model"] = events
            events = json.loads(json.dumps(original))
            events[1]["message"]["model"] = "claude-opus-test"
            scenarios["wrong-message-model"] = events
            for label, events in scenarios.items():
                with self.subTest(scenario=label):
                    parsed = claude.inspect_claude_stream(
                        "\n".join(map(json.dumps, events)), plugin, root, target, nonce, "claude-sonnet-test",
                    )
                    self.assertFalse(parsed["valid"], parsed)

    def test_codex_rejects_failed_commands_and_events_outside_the_turn(self) -> None:
        engine = import_script(CODEX_ENGINE, "layer2_codex_evidence_contract")
        marker = "CODEX_SKILL_SELECTED:demo-fixed"
        witnesses = codex_witness("demo", marker)
        original = [
            {"type": "thread.started", "thread_id": "fixture"},
            {"type": "turn.started"},
            {"type": "item.completed", "item": {"id": "message", "type": "agent_message", "text": "Done."}},
            {"type": "turn.completed"},
        ]
        scenarios = {}
        for label, status, exit_code in (("failed", "failed", 1), ("declined", "declined", None),
                                         ("nonzero", "completed", 2), ("unfinished", "in_progress", None),
                                         ("missing-exit", "completed", None)):
            events = json.loads(json.dumps(original))
            events.insert(2, {"type": "item.completed", "item": {
                "id": "read", "type": "command_execution", "command": "cat .agents/skills/demo/SKILL.md",
                "status": status, "exit_code": exit_code, "aggregated_output": "unavailable",
            }})
            scenarios[label] = events
        events = json.loads(json.dumps(original))
        events.append({"type": "item.completed", "item": {"id": "late", "type": "agent_message", "text": marker}})
        scenarios["trailing-marker"] = events
        events = json.loads(json.dumps(original))
        events.insert(1, {"type": "item.completed", "item": {"id": "early", "type": "agent_message", "text": marker}})
        scenarios["before-turn"] = events
        for label, events in scenarios.items():
            with self.subTest(scenario=label):
                parsed = engine.inspect_codex_jsonl(
                    "\n".join(map(json.dumps, events)), "demo", witnesses,
                )
                self.assertFalse(parsed["valid"], parsed)

    def test_claude_child_environment_controls(self) -> None:
        claude = import_script(CLAUDE_RUNNER, "layer2_claude_child_environment")
        with (
            mock.patch.dict(os.environ, {"FORCE_AUTOUPDATE_PLUGINS": "1", "L2_ENV_SENTINEL": "unchanged"}),
            mock.patch.object(claude.shutil, "which", return_value="/stub/claude"),
            mock.patch.object(claude.subprocess, "Popen", return_value=FakePopen(b"raw")) as launch,
            mock.patch.object(claude, "cleanup_child", create=True),
        ):
            original = os.environ.copy()
            claude.run_claude_query(
                "/stub/claude", Path("/tmp"), Path("/tmp/empty-mcp.json"), "q", "sonnet", 1,
                expected_skill="fixture:target",
            )
            environment = launch.call_args.kwargs["env"]
            self.assertEqual(environment.get("DISABLE_AUTOUPDATER"), "1")
            self.assertEqual(environment.get("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"), "1")
            self.assertEqual(environment.get("CLAUDE_CODE_MAX_RETRIES"), "0")
            self.assertNotIn("FORCE_AUTOUPDATE_PLUGINS", environment)
            self.assertNotIn("L2_ENV_SENTINEL", environment)
            self.assertEqual(environment, claude.claude_environment())
            self.assertTrue(dict(os.environ) == original, "parent environment changed")

    @unittest.skipIf(os.name == "nt", "POSIX process-group contract")
    def test_claude_exited_leader_still_signals_owned_group(self) -> None:
        claude = import_script(CLAUDE_RUNNER, "layer2_claude_exited_leader")
        child = FakePopen(b"", returncode=0)
        with mock.patch.object(claude.os, "killpg") as killpg:
            claude.terminate_child(child, signal.SIGTERM)
        killpg.assert_called_once_with(child.pid, signal.SIGTERM)

    def test_claude_cleanup_failure_retains_raw_and_stops(self) -> None:
        claude = import_script(CLAUDE_RUNNER, "layer2_claude_cleanup_failure")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "speckit-pro" / "skills" / "demo" / "SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text("---\nname: demo\ndescription: Fixture.\n---\nNonce body.\n", encoding="utf-8")
            corpus = root / "tests" / "speckit-pro" / "layer2-trigger" / "evals" / "demo-trigger.json"
            corpus.parent.mkdir(parents=True)
            corpus.write_text('[{"query":"q","should_trigger":true}]\n', encoding="utf-8")
            claude.PLUGIN_ROOT = root / "speckit-pro"
            raw, error = b"raw-before-cleanup\r\n", b"stderr-before-cleanup\xff"
            for outcome in ("cleanup-failure", "signal-failure", "unexpected-descendants"):
                with self.subTest(outcome=outcome):
                    interrupted = outcome == "signal-failure"
                    unexpected = outcome == "unexpected-descendants"
                    evidence = root / f"evidence-{outcome}"
                    child = FakePopen(raw, error)
                    if interrupted:
                        child.communicate = mock.Mock(side_effect=[claude.TerminationRequested(signal.SIGTERM), (raw, error)])
                    observed = [{"pgid": child.pid, "errno": 1, "elapsed_seconds": 0.01}]
                    if unexpected:
                        observed.append({"pgid": child.pid, "errno": 3, "elapsed_seconds": 0.02})

                    def cleanup(_child: object, *, observations: list[dict[str, object]]) -> bool:
                        observations.extend(observed)
                        if not unexpected:
                            raise PermissionError("owned group probe denied")
                        return True

                    previous_handler = signal.getsignal(signal.SIGTERM)
                    with (
                        mock.patch.object(claude.shutil, "which", return_value="/stub/claude"),
                        mock.patch.object(claude, "cli_preflight", return_value=({}, "ok")),
                        mock.patch.object(claude.subprocess, "Popen", return_value=child) as launch,
                        mock.patch.object(claude, "cleanup_child", side_effect=cleanup),
                        mock.patch.object(claude, "inspect_claude_stream", return_value={"valid": True, "selected": True}) as inspect,
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        code = claude.main(["demo", "--evidence-dir", str(evidence)])
                    self.assertEqual(code, 143 if interrupted else 1)
                    self.assertEqual(launch.call_count, 1, "cleanup failure launched another trial")
                    inspect.assert_called_once()
                    self.assertEqual((evidence / "case-001-trial-01.jsonl").read_bytes(), raw)
                    self.assertEqual((evidence / "case-001-trial-01.stderr.log").read_bytes(), error)
                    failure = json.loads((evidence / "case-001-trial-01.failure.json").read_text(encoding="utf-8"))
                    self.assertFalse(failure["valid"])
                    self.assertEqual(failure["cleanup_verified"], unexpected)
                    self.assertEqual(failure["exit_code"], 0)
                    self.assertEqual(failure["child_pid"], child.pid)
                    self.assertEqual(failure["child_pgid"], child.pid if os.name != "nt" else None)
                    self.assertEqual(failure["cleanup_observations"], observed)
                    self.assertEqual(failure["interrupted_by_signal"], signal.SIGTERM if interrupted else None)
                    if unexpected:
                        self.assertTrue(failure["unexpected_descendants"])
                        self.assertIn("lingering owned descendants", failure["reason"])
                        self.assertIsNone(failure["cleanup_error"])
                    else:
                        self.assertIn("owned group probe denied", failure["cleanup_error"])
                    self.assertIsNone(claude.ACTIVE_CHILD)
                    self.assertEqual(signal.getsignal(signal.SIGTERM), previous_handler)

    @unittest.skipIf(os.name == "nt", "POSIX process-group contract")
    def test_claude_cleanup_rejects_probe_failure_and_supervisor_group(self) -> None:
        claude = import_script(CLAUDE_RUNNER, "layer2_claude_cleanup_guards")
        child = FakePopen(b"", returncode=0)
        with (
            mock.patch.object(claude.os, "getpgrp", return_value=child.pid + 1),
            mock.patch.object(claude.os, "killpg", side_effect=PermissionError("probe denied")) as killpg,
        ):
            with self.assertRaises(PermissionError):
                claude.cleanup_child(child)
            killpg.assert_called_once_with(child.pid, 0)
        with (
            mock.patch.object(claude.os, "getpgrp", return_value=child.pid),
            mock.patch.object(claude.os, "killpg") as killpg,
        ):
            with self.assertRaisesRegex(OSError, "unowned process group"):
                claude.cleanup_child(child)
            with self.assertRaisesRegex(OSError, "unowned process group"):
                claude.terminate_child(child)
            killpg.assert_not_called()

    @unittest.skipIf(os.name == "nt", "POSIX process-group contract")
    def test_claude_completed_group_may_exit_during_grace_without_signals(self) -> None:
        claude = import_script(CLAUDE_RUNNER, "layer2_claude_natural_group_exit")
        child = FakePopen(b"", returncode=0)
        with (
            mock.patch.object(claude.os, "getpgrp", return_value=child.pid + 1),
            mock.patch.object(claude.os, "killpg", side_effect=[None, ProcessLookupError(), ProcessLookupError()]) as killpg,
            mock.patch.object(claude.time, "sleep"),
        ):
            self.assertFalse(claude.cleanup_child(child))
        self.assertTrue(all(call.args == (child.pid, 0) for call in killpg.call_args_list))

    @unittest.skipIf(os.name == "nt", "POSIX process-group contract")
    def test_claude_post_kill_permission_probe_requires_later_absence(self) -> None:
        claude = import_script(CLAUDE_RUNNER, "layer2_claude_post_kill_probe")
        for persistent in (False, True):
            with self.subTest(persistent=persistent):
                child = FakePopen(b"", returncode=0)
                sent = []
                post_kill_probes = 0
                observations = []

                def probe(pgid: int, signum: int) -> None:
                    nonlocal post_kill_probes
                    self.assertEqual(pgid, child.pid)
                    if signum:
                        sent.append(signum)
                    elif signal.SIGKILL in sent:
                        post_kill_probes += 1
                        if persistent or post_kill_probes == 1:
                            raise PermissionError(1, "post-kill probe unresolved")
                        raise ProcessLookupError(3, "group absent")

                with (
                    mock.patch.object(claude.os, "getpgrp", return_value=child.pid + 1),
                    mock.patch.object(claude.os, "killpg", side_effect=probe),
                    mock.patch.object(claude, "CLEANUP_TIMEOUT", 0.5),
                    mock.patch.object(claude, "DESCENDANT_EXIT_GRACE", 0),
                    mock.patch.object(claude.time, "monotonic", side_effect=[i / 10 for i in range(100)]),
                    mock.patch.object(claude.time, "sleep"),
                ):
                    if persistent:
                        with self.assertRaisesRegex(OSError, "post-kill probe unresolved"):
                            claude.cleanup_child(child, observations=observations)
                    else:
                        self.assertTrue(claude.cleanup_child(child, observations=observations))
                self.assertEqual(sent, [signal.SIGTERM, signal.SIGKILL])
                self.assertGreaterEqual(post_kill_probes, 2)
                self.assertEqual(observations[0]["errno"], 1)
                self.assertEqual(observations[0]["pgid"], child.pid)
                self.assertEqual(observations[-1]["errno"], 1 if persistent else 3)

    @unittest.skipIf(os.name == "nt", "POSIX process-group contract")
    def test_claude_only_post_successful_kill_eperm_may_settle(self) -> None:
        claude = import_script(CLAUDE_RUNNER, "layer2_claude_permission_boundaries")
        for fault in ("initial", "term-send", "term-probe", "kill-send", "kill-absent", "post-kill-eacces"):
            with self.subTest(fault=fault):
                child = FakePopen(b"", returncode=0)
                attempted = []
                failed_probes = []

                def probe(_pgid: int, signum: int) -> None:
                    if signum:
                        attempted.append(signum)
                        if (fault == "term-send" and signum == signal.SIGTERM) or (fault == "kill-send" and signum == signal.SIGKILL):
                            raise PermissionError(1, "signal send denied")
                        if fault == "kill-absent" and signum == signal.SIGKILL:
                            raise ProcessLookupError(3, "signal target absent")
                    elif (
                        (fault == "initial" and not attempted)
                        or (fault == "term-probe" and attempted == [signal.SIGTERM])
                        or (fault in {"kill-absent", "post-kill-eacces"} and signal.SIGKILL in attempted)
                    ):
                        failed_probes.append(signum)
                        raise PermissionError(13 if fault == "post-kill-eacces" else 1, "probe denied")

                with (
                    mock.patch.object(claude.os, "getpgrp", return_value=child.pid + 1),
                    mock.patch.object(claude.os, "killpg", side_effect=probe),
                    mock.patch.object(claude, "CLEANUP_TIMEOUT", 0.5),
                    mock.patch.object(claude, "DESCENDANT_EXIT_GRACE", 0),
                    mock.patch.object(claude.time, "monotonic", side_effect=[i / 10 for i in range(100)]),
                    mock.patch.object(claude.time, "sleep"),
                ):
                    with self.assertRaises(PermissionError):
                        claude.cleanup_child(child)
                self.assertLessEqual(len(failed_probes), 1, "an ineligible permission error entered settling polls")

    def test_claude_finally_cleanup_covers_normal_timeout_and_interruption(self) -> None:
        claude = import_script(CLAUDE_RUNNER, "layer2_claude_finally_cleanup")
        for mode in ("normal", "timeout", "interruption"):
            with self.subTest(mode=mode):
                child = FakePopen(b"partial\r\n", b"partial-error\xff")
                if mode == "timeout":
                    child.timeout = True
                elif mode == "interruption":
                    child.communicate = mock.Mock(side_effect=[claude.TerminationRequested(signal.SIGTERM), (b"partial\r\n", b"partial-error\xff")])
                with (
                    mock.patch.object(claude.shutil, "which", return_value="/stub/claude"),
                    mock.patch.object(claude.subprocess, "Popen", return_value=child),
                    mock.patch.object(claude, "terminate_child"),
                    mock.patch.object(claude, "cleanup_child", create=True) as cleanup,
                ):
                    if mode == "interruption":
                        with self.assertRaises(claude.TerminationRequested) as raised:
                            claude.run_claude_query("/stub/claude", Path("/tmp"), Path("/tmp/empty"), "q", "sonnet", 1, expected_skill="fixture:target")
                        self.assertEqual(raised.exception.stdout, b"partial\r\n")
                        self.assertEqual(raised.exception.stderr, b"partial-error\xff")
                    else:
                        result = claude.run_claude_query("/stub/claude", Path("/tmp"), Path("/tmp/empty"), "q", "sonnet", 1, expected_skill="fixture:target")
                        self.assertEqual(result, (-1 if mode == "timeout" else 0, b"partial\r\n", b"partial-error\xff", mode == "timeout"))
                    cleanup.assert_called_once_with(child, observations=[])
                    self.assertIsNone(claude.ACTIVE_CHILD)

    def test_claude_repeated_drain_timeout_is_bounded_and_retains_partial_output(self) -> None:
        claude = import_script(CLAUDE_RUNNER, "layer2_claude_bounded_drain")
        child = FakePopen(b"partial", b"error")
        child.communicate = mock.Mock(side_effect=subprocess.TimeoutExpired(["stub"], 1, output=b"partial", stderr=b"error"))
        with (
            mock.patch.object(claude.shutil, "which", return_value="/stub/claude"),
            mock.patch.object(claude.subprocess, "Popen", return_value=child),
            mock.patch.object(claude, "terminate_child"),
            mock.patch.object(claude, "cleanup_child", create=True),
        ):
            with self.assertRaises(OSError) as raised:
                claude.run_claude_query("/stub/claude", Path("/tmp"), Path("/tmp/empty"), "q", "sonnet", 1, expected_skill="fixture:target")
        self.assertEqual(raised.exception.stdout, b"partial")
        self.assertEqual(raised.exception.stderr, b"error")
        self.assertTrue(raised.exception.timed_out)
        self.assertTrue(all(call.kwargs.get("timeout") is not None for call in child.communicate.call_args_list))
        self.assertIsNone(claude.ACTIVE_CHILD)

    def test_claude_signal_during_cleanup_preserves_completed_stream(self) -> None:
        claude = import_script(CLAUDE_RUNNER, "layer2_claude_cleanup_signal")
        with (
            mock.patch.object(claude.shutil, "which", return_value="/stub/claude"),
            mock.patch.object(claude.subprocess, "Popen", return_value=FakePopen(b"completed", b"raw-error")),
            mock.patch.object(claude, "cleanup_child", side_effect=claude.TerminationRequested(signal.SIGTERM)),
        ):
            with self.assertRaises(claude.TerminationRequested) as raised:
                claude.run_claude_query("/stub/claude", Path("/tmp"), Path("/tmp/empty"), "q", "sonnet", 1, expected_skill="fixture:target")
        self.assertEqual(raised.exception.stdout, b"completed")
        self.assertEqual(raised.exception.stderr, b"raw-error")
        self.assertIn("interrupted", raised.exception.cleanup_error)
        self.assertIsNone(claude.ACTIVE_CHILD)

    def test_claude_skill_isolation(self) -> None:
        claude = import_script(CLAUDE_RUNNER, "layer2_claude_skill_isolation")
        root = Path("/tmp/measurement-plugin")
        plugin = "skill-catalog-eval-fixed"
        target = f"{plugin}:demo-eval-fixed"
        nonce = "CLAUDE_SKILL_SELECTED_fixed"
        raw = claude_stream(root, plugin, target, nonce)
        argument_events = [json.loads(line) for line in raw.splitlines()]
        argument_events[1]["message"]["content"][0]["input"]["args"] = "additional context"
        argument_result = claude.inspect_claude_stream(
            "\n".join(json.dumps(event) for event in argument_events), plugin, root, target, nonce, "sonnet"
        )
        self.assertTrue(argument_result["valid"] and argument_result["selected"])
        for identifier in ({"bad": "id"}, ["bad"], 1, 1.5, True, None, ""):
            with self.subTest(tool_use_id=identifier):
                events = [json.loads(line) for line in raw.splitlines()]
                use = events[1]["message"]["content"][0]
                use["id"] = identifier
                self.assertEqual(
                    claude.skill_results_error(events, [(1, use)], 0, len(events) - 1),
                    "malformed Skill tool use identity",
                )
                parsed = claude.inspect_claude_stream(
                    "\n".join(json.dumps(event) for event in events), plugin, root, target, nonce, "sonnet"
                )
                self.assertFalse(parsed["valid"])
                self.assertFalse(parsed["selected"])
                self.assertIn("malformed", parsed["reason"])
        for label, mutate in {
            "missing skill catalog": lambda events: events[0].pop("skills"),
            "empty skill catalog": lambda events: events[0].update(skills=[]),
            "duplicate target catalog": lambda events: events[0].update(skills=[target, target]),
            "bundled skill catalog": lambda events: events[0].update(skills=[target, "code-review"]),
            "nested target selection": lambda events: events[1].update(parent_tool_use_id="outer-review"),
        }.items():
            with self.subTest(label=label):
                events = [json.loads(line) for line in raw.splitlines()]
                mutate(events)
                parsed = claude.inspect_claude_stream(
                    "\n".join(json.dumps(event) for event in events), plugin, root, target, nonce, "sonnet"
                )
                self.assertFalse(parsed["valid"])

        # Sanitized shape of the observed unrelated bundled-skill expansion.
        events = [json.loads(line) for line in raw.splitlines()]
        events[0]["skills"].append("code-review")
        events[1]["message"]["content"][0]["input"]["skill"] = "code-review"
        nested = json.loads(json.dumps(events[1]))
        nested["parent_tool_use_id"] = "toolu-skill"
        nested["message"]["model"] = "claude-sonnet-4-6"
        events.insert(2, nested)
        parsed = claude.inspect_claude_stream(
            "\n".join(json.dumps(event) for event in events), plugin, root, target, nonce, "sonnet"
        )
        self.assertFalse(parsed["valid"])

        attempted = []
        prepared = []

        def guarded_launch(command: list[str], **kwargs: object) -> FakePopen:
            # This is an argv canary, not proof of the installed CLI's permission semantics.
            allow_index = command.index("--allowedTools") + 1
            self.assertEqual(
                command[allow_index:allow_index + 4],
                [
                    f"Skill({target})", f"Skill({target} *)",
                    f"Skill({plugin}:no-speckit-skill)", f"Skill({plugin}:no-speckit-skill *)",
                ],
            )
            self.assertEqual(command[command.index("--permission-mode") + 1], "dontAsk")
            self.assertEqual(command[command.index("--permission-prompts") + 1], "none")
            self.assertEqual(command[command.index("--setting-sources") + 1], "")
            self.assertEqual(json.loads(command[command.index("--settings") + 1]), {
                "disableBundledSkills": True, "skillOverrides": {"doctor": "off"},
                "permissions": {"deny": [
                    "Skill(init)", "Skill(init *)", "Skill(security-review)", "Skill(security-review *)"
                ]},
            })
            environment = claude.claude_environment()
            self.assertTrue(kwargs["env"] == environment, "launch environment differs from the approved child controls")
            prepared.append((command.copy(), kwargs))
            attempted.append(target)
            return FakePopen(raw)

        with (
            mock.patch.object(claude.shutil, "which", return_value="/usr/local/bin/claude"),
            mock.patch.object(claude.subprocess, "Popen", side_effect=guarded_launch),
            mock.patch.object(claude, "cleanup_child"),
        ):
            claude.run_claude_query(
                "/usr/local/bin/claude", root, root / "empty-mcp.json", "query", "sonnet", 30,
                expected_skill=target,
            )
        self.assertEqual(attempted, [target])
        unsafe_command, launch_kwargs = prepared[0]
        unsafe_command[unsafe_command.index("--allowedTools") + 1] = "Skill"
        with self.assertRaises(AssertionError):
            guarded_launch(unsafe_command, **launch_kwargs)
        self.assertEqual(attempted, [target], "unsafe argv reached the mock executor")

    def test_claude_direct_runner_contracts(self) -> None:
        claude = import_script(CLAUDE_RUNNER, "layer2_claude_direct")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source" / "SKILL.md"
            source.parent.mkdir()
            source.write_text(
                "---\nname: demo\ndescription: Exact source description.\nargument-hint: x\n---\n\nFull body must not copy.\n",
                encoding="utf-8",
            )
            plugin_root = root / "staged-plugin"
            plugin_name = "skill-catalog-eval-fixed"
            skill_name = "demo-eval-fixed"
            nonce = "CLAUDE_SKILL_SELECTED_fixed"
            staged_skill, expected_skill = claude.stage_measurement_plugin(
                source,
                plugin_root,
                plugin_name,
                skill_name,
                nonce,
            )
            staged_text = (staged_skill / "SKILL.md").read_text(encoding="utf-8")
            no_speckit_text = (
                plugin_root / "skills" / "no-speckit-skill" / "SKILL.md"
            ).read_text(encoding="utf-8")
            stream = claude_stream(plugin_root, plugin_name, expected_skill, nonce)
            selected = claude.inspect_claude_stream(
                stream,
                plugin_name,
                plugin_root,
                expected_skill,
                nonce,
                "claude-sonnet-test",
            )
            nonselected_stream = claude_stream(
                plugin_root,
                plugin_name,
                expected_skill,
                nonce,
                selected=False,
                model=None,
            )
            nonselected = claude.inspect_claude_stream(
                nonselected_stream,
                plugin_name,
                plugin_root,
                expected_skill,
                nonce,
                "claude-sonnet-test",
            )
            end_conversation_events = [
                json.loads(line) for line in stream.decode("utf-8").splitlines()
            ]
            end_conversation_events[0]["tools"] = ["Skill", "EndConversation"]
            end_conversation = claude.inspect_claude_stream(
                ("\n".join(json.dumps(event) for event in end_conversation_events) + "\n").encode("utf-8"),
                plugin_name,
                plugin_root,
                expected_skill,
                nonce,
                "claude-sonnet-test",
            )
            empty_response_events = [
                json.loads(line) for line in nonselected_stream.decode("utf-8").splitlines()
            ]
            empty_response_events[1]["message"]["content"] = []
            empty_response = claude.inspect_claude_stream(
                ("\n".join(json.dumps(event) for event in empty_response_events) + "\n").encode("utf-8"),
                plugin_name,
                plugin_root,
                expected_skill,
                nonce,
                "claude-sonnet-test",
            )

            def inspect_mutation(transform: object) -> dict[str, object]:
                events = [json.loads(line) for line in stream.decode("utf-8").splitlines()]
                assert callable(transform)
                transform(events)
                raw = ("\n".join(json.dumps(event) for event in events) + "\n").encode("utf-8")
                return claude.inspect_claude_stream(
                    raw,
                    plugin_name,
                    plugin_root,
                    expected_skill,
                    nonce,
                    "claude-sonnet-test",
                )

            def blocks(events: list[dict[str, object]]) -> tuple[dict[str, object], dict[str, object]]:
                tool_use = events[1]["message"]["content"][0]
                tool_result = events[2]["message"]["content"][0]
                assert isinstance(tool_use, dict) and isinstance(tool_result, dict)
                return tool_use, tool_result

            mutations = {
                "wrong plugin": lambda events: events[0]["plugins"][0].update(name="other"),
                "missing init": lambda events: events.pop(0),
                "selection before init": lambda events: events.insert(1, events.pop(0)),
                "plugin error": lambda events: events[0].update(
                    plugin_errors=[{"plugin": plugin_name, "message": "failed"}]
                ),
                "unexpected MCP": lambda events: events[0].update(mcp_servers=[{"name": "extra"}]),
                "missing tools": lambda events: events[0].pop("tools"),
                "malformed tools": lambda events: events[0].update(tools=["Skill", {"name": "Grep"}]),
                "duplicate tools": lambda events: events[0].update(tools=["Skill", "Skill"]),
                "missing Skill": lambda events: events[0].update(tools=["EndConversation"]),
                "broader tools": lambda events: events[0].update(tools=["Skill", "Grep"]),
                "malformed skill input": lambda events: blocks(events)[0].update(input={}),
                "competing skill": lambda events: blocks(events)[0].update(input={"skill": "other:skill"}),
                "missing tool result": lambda events: events.pop(2),
                "errored tool result": lambda events: blocks(events)[1].update(is_error=True),
                "terminal error": lambda events: events[-1].update(subtype="error", is_error=True),
                "permission denial": lambda events: events.insert(
                    -1, {"type": "permission_denied", "tool_name": "Skill"}
                ),
                "terminal permission denial": lambda events: events[-1].update(
                    permission_denials=[{"tool_name": "Skill"}]
                ),
                "API retry": lambda events: events.insert(
                    -1, {"type": "system", "subtype": "api_retry", "error": "model_not_found"}
                ),
            }
            mutation_results = {name: inspect_mutation(transform) for name, transform in mutations.items()}

            nonce_only = claude.inspect_claude_stream(
                nonselected_stream.replace(b"No skill selected.", nonce.encode("utf-8")),
                plugin_name,
                plugin_root,
                expected_skill,
                nonce,
                "claude-sonnet-test",
            )
            no_nonce = claude.inspect_claude_stream(
                stream.replace(nonce.encode("utf-8"), b"ordinary response"),
                plugin_name,
                plugin_root,
                expected_skill,
                nonce,
                "claude-sonnet-test",
            )
            invalid_utf8 = stream + b"\xff"
            invalid_utf8_result = claude.inspect_claude_stream(
                invalid_utf8,
                plugin_name,
                plugin_root,
                expected_skill,
                nonce,
                "claude-sonnet-test",
            )

            evidence_dir = root / "evidence"
            evidence_dir.mkdir()
            raw_evidence = claude.retain_trial_evidence(
                evidence_dir,
                1,
                1,
                stream,
                b"stderr\r\n\xff",
            )

            fake = FakePopen(stream, b"warning\r\n")
            captured: dict[str, object] = {}
            mcp_config = plugin_root / "empty-mcp.json"
            claude.write_empty_mcp_config(mcp_config)

            def fake_popen(command: list[str], **kwargs: object) -> FakePopen:
                captured["command"] = command
                captured["kwargs"] = kwargs
                return fake

            launch_evidence: dict[str, object] = {}
            with (
                mock.patch.object(claude.shutil, "which", return_value="/usr/local/bin/claude"),
                mock.patch.object(claude.subprocess, "Popen", side_effect=fake_popen),
                mock.patch.object(claude, "cleanup_child"),
            ):
                rc, launched_stdout, launched_stderr, timed_out = claude.run_claude_query(
                    "/usr/local/bin/claude",
                    plugin_root,
                    mcp_config,
                    "query",
                    "claude-sonnet-test",
                    30,
                    expected_skill=expected_skill,
                    process_evidence=launch_evidence,
                )

            missing_tool_preflights = []
            doctor_output = (
                f"{claude.PINNED_DOCTOR_RUNNING}\n"
                f"{claude.PINNED_MANAGED_SETTINGS}\n"
                f"{claude.PINNED_ORGANIZATION_POLICY}\n"
            ).encode("utf-8")
            managed_preferences_output = claude.plistlib.dumps({})
            for omitted_flag in (
                "--tools", "--allowedTools", "--settings", "--setting-sources",
                "--permission-mode", "--permission-prompts",
            ):
                supported_help = " ".join(
                    flag for flag in claude.REQUIRED_FLAGS if flag != omitted_flag
                ).encode("utf-8")
                with (
                    mock.patch.object(claude.shutil, "which", return_value="/usr/local/bin/claude"),
                    mock.patch.object(claude.sys, "platform", "darwin"),
                    mock.patch.object(claude, "MACOS_MANAGED_ROOT", root / "managed"),
                    mock.patch.object(
                        claude.subprocess,
                        "run",
                        side_effect=[
                            SimpleNamespace(
                                returncode=0,
                                stdout=f"{claude.PINNED_CLAUDE_VERSION}\n".encode("utf-8"),
                                stderr=b"",
                            ),
                            SimpleNamespace(returncode=0, stdout=supported_help, stderr=b""),
                            SimpleNamespace(returncode=0, stdout=doctor_output, stderr=b""),
                            SimpleNamespace(returncode=0, stdout=managed_preferences_output, stderr=b""),
                        ],
                    ),
                ):
                    missing_tool_preflights.append(claude.cli_preflight("/usr/local/bin/claude"))

            supported_help = " ".join(claude.REQUIRED_FLAGS).encode("utf-8")
            qualified_outputs = [
                SimpleNamespace(
                    returncode=0,
                    stdout=f"{claude.PINNED_CLAUDE_VERSION}\n".encode("utf-8"),
                    stderr=b"",
                ),
                SimpleNamespace(returncode=0, stdout=supported_help, stderr=b""),
                SimpleNamespace(returncode=0, stdout=doctor_output, stderr=b""),
                SimpleNamespace(returncode=0, stdout=managed_preferences_output, stderr=b""),
            ]
            with (
                mock.patch.object(claude.shutil, "which", return_value="/usr/local/bin/claude"),
                mock.patch.object(claude.sys, "platform", "darwin"),
                mock.patch.object(claude, "MACOS_MANAGED_ROOT", root / "managed"),
                mock.patch.object(claude.subprocess, "run", side_effect=qualified_outputs) as preflight_calls,
            ):
                qualified_preflight = claude.cli_preflight("/usr/local/bin/claude")
            unqualified_doctor = doctor_output.replace(
                claude.PINNED_MANAGED_SETTINGS.encode("utf-8"),
                b"Managed settings (remote): active",
            )
            with (
                mock.patch.object(claude.shutil, "which", return_value="/usr/local/bin/claude"),
                mock.patch.object(claude.sys, "platform", "darwin"),
                mock.patch.object(claude, "MACOS_MANAGED_ROOT", root / "managed"),
                mock.patch.object(claude.subprocess, "run", side_effect=[
                    *qualified_outputs[:2],
                    SimpleNamespace(returncode=0, stdout=unqualified_doctor, stderr=b""),
                    SimpleNamespace(returncode=0, stdout=managed_preferences_output, stderr=b""),
                ]),
            ):
                rejected_managed_preflight = claude.cli_preflight("/usr/local/bin/claude")
            managed_root = root / "managed-present"
            managed_root.mkdir()
            (managed_root / "CLAUDE.md").write_text("managed instruction\n", encoding="utf-8")
            with (
                mock.patch.object(claude.shutil, "which", return_value="/usr/local/bin/claude"),
                mock.patch.object(claude.sys, "platform", "darwin"),
                mock.patch.object(claude, "MACOS_MANAGED_ROOT", managed_root),
                mock.patch.object(claude.subprocess, "run", side_effect=qualified_outputs),
            ):
                rejected_managed_file_preflight = claude.cli_preflight("/usr/local/bin/claude")

            preflight_identity_rejections = []
            for discovered, expected_reason in (
                (None, "Claude CLI disappeared before preflight"),
                ("/different/bin/claude", "Claude runtime changed before preflight"),
            ):
                with (
                    mock.patch.object(claude.shutil, "which", return_value=discovered) as discovery,
                    mock.patch.object(claude.subprocess, "run") as preflight_run,
                ):
                    result = claude.cli_preflight("/usr/local/bin/claude")
                preflight_identity_rejections.append(
                    (result, expected_reason, discovery.call_args_list, preflight_run.call_count)
                )

            query_identity_rejections = []
            for discovered, expected_exception, expected_error in (
                (None, OSError, "Claude CLI disappeared after initial resolution"),
                (
                    "/different/bin/claude",
                    ValueError,
                    "Claude runtime changed after initial resolution",
                ),
            ):
                with (
                    mock.patch.object(claude.shutil, "which", return_value=discovered) as discovery,
                    mock.patch.object(claude.subprocess, "Popen") as rejected_popen,
                ):
                    try:
                        claude.run_claude_query(
                            "/usr/local/bin/claude",
                            plugin_root,
                            mcp_config,
                            "query",
                            "claude-sonnet-test",
                            30,
                            expected_skill=expected_skill,
                        )
                    except (OSError, ValueError) as exc:
                        result = (type(exc), str(exc))
                    else:
                        result = (None, "")
                query_identity_rejections.append(
                    (
                        result,
                        expected_exception,
                        expected_error,
                        discovery.call_args_list,
                        rejected_popen.call_count,
                    )
                )

            timeout_bytes = b'{"type":"system","subtype":"init"}\r\n'
            timeout_stderr = b"partial stderr\r\n"
            timeout_child = FakePopen(timeout_bytes, timeout_stderr)
            timeout_child.timeout = True
            with (
                mock.patch.object(claude.shutil, "which", return_value="/usr/local/bin/claude"),
                mock.patch.object(claude.subprocess, "Popen", return_value=timeout_child),
                mock.patch.object(claude, "cleanup_child") as timeout_cleanup,
            ):
                timeout_rc, timeout_stdout, timeout_error, timeout_state = claude.run_claude_query(
                    "/usr/local/bin/claude",
                    plugin_root,
                    plugin_root / "empty-mcp.json",
                    "query",
                    "claude-sonnet-test",
                    1,
                    expected_skill=expected_skill,
                )
            timeout_evidence_dir = root / "timeout-evidence"
            timeout_evidence_dir.mkdir()
            timeout_evidence = claude.retain_trial_evidence(
                timeout_evidence_dir,
                1,
                1,
                timeout_stdout,
                timeout_error,
            )

            corpus = root / "corpus.json"
            invalid_corpora = (
                "[]",
                "{}",
                "{",
                '[{"query":"q"}]',
                '[{"query":"q","should_trigger":true},{"query":"q","should_trigger":false}]',
            )
            corpus_results = []
            for body in invalid_corpora:
                corpus.write_text(body, encoding="utf-8")
                corpus_results.append(claude.load_eval_corpus(corpus)[0])

            main_fixture = root / "main-fixture"
            main_plugin = main_fixture / "speckit-pro"
            main_source = main_plugin / "skills" / "demo" / "SKILL.md"
            main_source.parent.mkdir(parents=True)
            main_source.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            main_corpus = main_fixture / "tests" / "speckit-pro" / "layer2-trigger" / "evals" / "demo-trigger.json"
            main_corpus.parent.mkdir(parents=True)
            main_corpus.write_text(
                json.dumps([{"query": "q", "should_trigger": True}]) + "\n",
                encoding="utf-8",
            )
            main_staged = root / "main-staged"
            main_evidence = root / "main-evidence"
            main_evidence.mkdir()
            fixed_id = "123456789abc"
            main_plugin_name = f"skill-catalog-eval-{fixed_id}"
            main_skill = f"{main_plugin_name}:demo-eval-{fixed_id}"
            main_nonce = f"CLAUDE_SKILL_SELECTED_{fixed_id}"
            main_stream = claude_stream(main_staged, main_plugin_name, main_skill, main_nonce)
            claude.PLUGIN_ROOT = main_plugin
            main_stdout = io.StringIO()
            with (
                mock.patch.object(claude.shutil, "which", return_value="/usr/local/bin/claude"),
                mock.patch.object(
                    claude,
                    "cli_preflight",
                    return_value=({"version": "2.1.261", "supported_flags": []}, "ok"),
                ),
                mock.patch.object(claude.uuid, "uuid4", return_value=SimpleNamespace(hex=fixed_id)),
                mock.patch.object(
                    claude.tempfile,
                    "mkdtemp",
                    side_effect=[str(main_staged), str(main_evidence)],
                ),
                mock.patch.object(
                    claude,
                    "run_claude_query",
                    side_effect=supervised_results(
                        [(0, main_stream, b"", False)] * 3, "claude-sonnet-test",
                    ),
                ) as main_run,
                contextlib.redirect_stdout(main_stdout),
            ):
                main_exit = claude.main(["demo", "--model", "claude-sonnet-test"])
            main_report = json.loads(main_stdout.getvalue())

            main_identity_rejections = []
            for case_index, (discovered, expected_error) in enumerate(
                (
                    (None, "Claude CLI disappeared after initial resolution"),
                    ("/different/bin/claude", "Claude runtime changed after initial resolution"),
                ),
                start=1,
            ):
                rejected_staged = root / f"rejected-staged-{case_index}"
                rejected_evidence = root / f"rejected-evidence-{case_index}"
                rejected_stdout = io.StringIO()
                rejected_stderr = io.StringIO()
                with (
                    mock.patch.object(
                        claude.shutil,
                        "which",
                        side_effect=["/usr/local/bin/claude", discovered],
                    ) as discovery,
                    mock.patch.object(
                        claude,
                        "cli_preflight",
                        return_value=({"version": "2.1.261", "supported_flags": []}, "ok"),
                    ),
                    mock.patch.object(
                        claude.uuid,
                        "uuid4",
                        return_value=SimpleNamespace(hex=f"{case_index:012d}"),
                    ),
                    mock.patch.object(claude.tempfile, "mkdtemp", return_value=str(rejected_staged)),
                    mock.patch.object(claude.subprocess, "Popen") as rejected_popen,
                    mock.patch.object(claude, "retain_trial_evidence") as rejected_retain,
                    contextlib.redirect_stdout(rejected_stdout),
                    contextlib.redirect_stderr(rejected_stderr),
                ):
                    rejected_exit = claude.main(
                        [
                            "demo",
                            "--model",
                            "claude-sonnet-test",
                            "--evidence-dir",
                            str(rejected_evidence),
                        ]
                    )
                main_identity_rejections.append(
                    (
                        rejected_exit,
                        rejected_stdout.getvalue(),
                        rejected_stderr.getvalue(),
                        expected_error,
                        discovery.call_args_list,
                        rejected_popen.call_count,
                        rejected_retain.call_count,
                        rejected_staged.exists(),
                        sorted(rejected_evidence.iterdir()),
                    )
                )

            checks = {
                "source description copied exactly": "description: Exact source description." in staged_text,
                "full functional body not copied": "Full body must not copy" not in staged_text,
                "minimal nonce body retained": nonce in staged_text,
                "measurement stub sentence opens body": staged_text.split("\n---\n", 1)[1].lstrip().startswith(
                    claude.MEASUREMENT_STUB_SENTENCE
                ),
                "no-op sibling staged": claude.NO_SPECKIT_SKILL_DESCRIPTION in no_speckit_text,
                "unique plugin manifest": json.loads(
                    (plugin_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
                )["name"] == plugin_name,
                "exact intended Skill selection": selected["valid"]
                and selected["selected"]
                and end_conversation["valid"]
                and end_conversation["selected"],
                "init supplies resolved model": selected["resolved_model"] == "claude-sonnet-test",
                "result model is not resolution evidence": nonselected["resolved_model"] is None,
                "completed response without Skill is valid": nonselected["valid"] and not nonselected["selected"],
                "empty completed assistant body is invalid": not empty_response["valid"],
                "nonce without native selection is invalid": not nonce_only["valid"],
                "native target selection requires nonce attestation": not no_nonce["valid"],
                "every malformed or competing selection fails": all(
                    not result["valid"] for result in mutation_results.values()
                ),
                "invalid UTF-8 fails semantic parsing": not invalid_utf8_result["valid"],
                "raw CRLF stdout retained byte-for-byte": Path(raw_evidence["stdout_path"]).read_bytes() == stream,
                "raw non-UTF8 stderr retained byte-for-byte": Path(raw_evidence["stderr_path"]).read_bytes()
                == b"stderr\r\n\xff",
                "raw hashes cover actual bytes": raw_evidence["stdout_sha256"] == hashlib.sha256(stream).hexdigest(),
                "direct argv uses restricted session plugin": captured["command"][:5]
                == ["/usr/local/bin/claude", "--restricted", "--setting-sources", "", "--plugin-dir"],
                "direct argv and preflight pin Skill-only tools": all(
                    flag in captured["command"]
                    for flag in ("--strict-mcp-config", "--mcp-config", "--model", "--output-format")
                )
                and captured["command"].count("--tools") == 1
                and captured["command"][captured["command"].index("--tools") + 1] == "Skill"
                and captured["command"].count("--allowedTools") == 1
                and captured["command"][captured["command"].index("--allowedTools") + 1] == f"Skill({expected_skill})"
                and f"Skill({plugin_name}:no-speckit-skill)" in captured["command"]
                and all(result is None for result, _reason in missing_tool_preflights),
                "preflight pins build and proves managed controls absent": qualified_preflight[0] is not None
                and qualified_preflight[0]["version"] == claude.PINNED_CLAUDE_VERSION
                and qualified_preflight[0]["request_retries"] == 0
                and all(qualified_preflight[0]["doctor_checks"].values())
                and rejected_managed_preflight[0] is None
                and rejected_managed_file_preflight[0] is None
                and all(call.kwargs["env"] == claude.claude_environment() for call in preflight_calls.call_args_list),
                "direct argv uses no persistence": "--no-session-persistence" in captured["command"],
                "direct launch inherits environment": captured["kwargs"]["env"].get("PATH") == os.environ.get("PATH"),
                "direct launch freezes settings and retries": launch_evidence["launch_contract"] == {
                    "config_isolated": True,
                    "retries_disabled": True,
                    "requested_model": "claude-sonnet-test",
                    "model_provider": "anthropic-claude-code",
                    "model_identity_evidence": "native-init-and-assistant-events",
                },
                "direct launch is confined to disposable root": Path(captured["kwargs"]["cwd"]).resolve()
                == plugin_root.resolve()
                and plugin_root.resolve() != Path.cwd().resolve()
                and mcp_config.is_file()
                and str(plugin_root) in captured["command"]
                and str(mcp_config) in captured["command"],
                "direct launch uses binary pipes": "text" not in captured["kwargs"],
                "direct launch result preserved": (rc, launched_stdout, launched_stderr, timed_out)
                == (0, stream, b"warning\r\n", False),
                "preflight rejects missing or changed Claude identity before subprocess": all(
                    result == (None, expected_reason)
                    and discovery_calls == [mock.call("claude")]
                    and run_calls == 0
                    for result, expected_reason, discovery_calls, run_calls in preflight_identity_rejections
                ),
                "query rejects missing or changed Claude identity before subprocess": all(
                    result == (expected_exception, expected_error)
                    and discovery_calls == [mock.call("claude")]
                    and popen_calls == 0
                    for (
                        result,
                        expected_exception,
                        expected_error,
                        discovery_calls,
                        popen_calls,
                    ) in query_identity_rejections
                ),
                "timeout preserves partial stdout": timeout_state and timeout_rc == -1 and timeout_stdout == timeout_bytes,
                "timeout preserves partial stderr": timeout_error == timeout_stderr,
                "timeout evidence hashes partial bytes": timeout_evidence["stdout_sha256"]
                == hashlib.sha256(timeout_bytes).hexdigest()
                and Path(timeout_evidence["stderr_path"]).read_bytes() == timeout_stderr,
                "timeout invokes owned process cleanup": timeout_cleanup.call_args_list == [mock.call(timeout_child, observations=[])],
                "negative one-of-three selection passes": claude.case_passes(False, selected=1, invalid=0),
                "negative two-of-three selection fails": not claude.case_passes(False, selected=2, invalid=0),
                "invalid evidence fails either polarity": not claude.case_passes(False, selected=0, invalid=1)
                and not claude.case_passes(True, selected=3, invalid=1),
                "empty, malformed, and duplicate corpora fail": all(result is None for result in corpus_results),
                "main executes exactly three trials per selected case": main_exit == 0
                and main_run.call_count == 3
                and len(list(main_evidence.glob("*.jsonl"))) == 3,
                "main report retains threshold and model metadata": main_report["metadata"]["runs_per_query"] == 3
                and main_report["metadata"]["trigger_threshold"] == 0.5
                and main_report["metadata"]["requested_model"] == "claude-sonnet-test",
                "main identity failures are controlled, cleaned, and never retained as provider trials": all(
                    exit_code == 1
                    and stdout == ""
                    and stderr == f"ERROR: {expected_error}\n"
                    and discovery_calls == [mock.call("claude"), mock.call("claude")]
                    and popen_calls == 0
                    and retain_calls == 0
                    and not staged_exists
                    and [path.name for path in evidence_files] == ["arm-cleanup.json"]
                    for (
                        exit_code,
                        stdout,
                        stderr,
                        expected_error,
                        discovery_calls,
                        popen_calls,
                        retain_calls,
                        staged_exists,
                        evidence_files,
                    ) in main_identity_rejections
                ),
                "Claude runner never mutates global paths": "shutil.move" not in CLAUDE_RUNNER.read_text(encoding="utf-8")
                and ".claude/" not in CLAUDE_RUNNER.read_text(encoding="utf-8")
                and "auth.json" not in CLAUDE_RUNNER.read_text(encoding="utf-8"),
            }
            for name, condition in checks.items():
                with self.subTest(msg=name):
                    self.assertTrue(condition)

    def test_claude_summary_requires_every_trial_model(self) -> None:
        claude = import_script(CLAUDE_RUNNER, "layer2_claude_model_summary")
        scenarios = (
            ("all-known-same", ("claude-sonnet-test",) * 3, "claude-sonnet-test"),
            ("mixed-known-missing", ("claude-sonnet-test", None, "claude-sonnet-test"), None),
            ("known-different", ("claude-sonnet-test", "claude-opus-test", "claude-sonnet-test"), None),
            ("all-missing", (None, None, None), None),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plugin = root / "fixture" / "speckit-pro"
            source = plugin / "skills" / "demo" / "SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text(
                "---\nname: demo\ndescription: Exact source description.\n---\n\nBody.\n",
                encoding="utf-8",
            )
            corpus = (
                root
                / "fixture"
                / "tests"
                / "speckit-pro"
                / "layer2-trigger"
                / "evals"
                / "demo-trigger.json"
            )
            corpus.parent.mkdir(parents=True)
            corpus.write_text(
                json.dumps([{"query": "q", "should_trigger": True}]) + "\n",
                encoding="utf-8",
            )
            claude.PLUGIN_ROOT = plugin

            for index, (label, models, expected) in enumerate(scenarios, start=1):
                with self.subTest(label=label):
                    fixed_id = f"{index:012d}"
                    staged = root / f"{label}-staged"
                    evidence = root / f"{label}-evidence"
                    evidence.mkdir()
                    plugin_name = f"skill-catalog-eval-{fixed_id}"
                    expected_skill = f"{plugin_name}:demo-eval-{fixed_id}"
                    nonce = f"CLAUDE_SKILL_SELECTED_{fixed_id}"
                    trial_results = [
                        (
                            0,
                            claude_stream(
                                staged,
                                plugin_name,
                                expected_skill,
                                nonce,
                                model=model,
                            ),
                            b"",
                            False,
                        )
                        for model in models
                    ]
                    output = io.StringIO()
                    with (
                        mock.patch.object(
                            claude.shutil,
                            "which",
                            return_value="/usr/local/bin/claude",
                        ),
                        mock.patch.object(
                            claude,
                            "cli_preflight",
                            return_value=({"version": "2.1.261", "supported_flags": []}, "ok"),
                        ),
                        mock.patch.object(
                            claude.uuid,
                            "uuid4",
                            return_value=SimpleNamespace(hex=fixed_id),
                        ),
                        mock.patch.object(
                            claude.tempfile,
                            "mkdtemp",
                            side_effect=[str(staged), str(evidence)],
                        ),
                        mock.patch.object(
                            claude,
                            "run_claude_query",
                            side_effect=supervised_results(trial_results, "claude-sonnet-test"),
                        ),
                        contextlib.redirect_stdout(output),
                    ):
                        exit_code = claude.main(["demo", "--model", "claude-sonnet-test"])
                    report = json.loads(output.getvalue())
                    self.assertEqual(exit_code, 0 if label == "all-known-same" else 1)
                    self.assertEqual(report["summary"]["resolved_model"], expected)

    def test_codex_process_stdin_isolated_from_positional_prompt(self) -> None:
        engine = import_script(CODEX_ENGINE, "layer2_codex_stdin_isolation")
        captured: dict[str, object] = {}

        def launch(_command: list[str], **kwargs: object) -> FakePopen:
            stdin = kwargs["stdin"]
            captured["stdin"] = stdin
            captured["stdin_is_terminal_at_launch"] = (
                isinstance(stdin, int) and stdin >= 0 and os.isatty(stdin)
            )
            return FakePopen(b"")

        launch_evidence: dict[str, object] = {}
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            engine.subprocess, "Popen", side_effect=launch,
        ), mock.patch.object(engine.processes, "cleanup_child"):
            result = engine.run_codex_query(
                Path(temporary), "query", "low", "gpt-5.6-sol", 30, [],
                process_evidence=launch_evidence,
            )

        self.assertEqual(result, (0, b"", b"", False))
        self.assertTrue(launch_evidence["launch_contract"]["stdin_prompt_isolated"])
        if os.name == "nt":
            self.assertEqual(captured["stdin"], subprocess.DEVNULL)
        else:
            self.assertTrue(captured["stdin_is_terminal_at_launch"])
            with self.assertRaises(OSError):
                os.fstat(captured["stdin"])

    def test_codex_symlink_path_uses_canonical_executable_without_environment_mutation(self) -> None:
        engine = import_script(CODEX_ENGINE, "layer2_codex_symlink_executable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            native = root / "native" / "codex"
            native.parent.mkdir()
            native.write_text("synthetic executable fixture\n")
            native.chmod(0o700)
            alias = root / "aliases" / "codex"
            alias.parent.mkdir()
            alias.symlink_to(native)
            with mock.patch.dict(os.environ, {"PATH": str(alias.parent)}), mock.patch.object(
                engine.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b"[]", b""),
            ) as execute, mock.patch.object(engine, "inspect_catalog_prompt", return_value=({}, "fixture")), mock.patch.object(
                engine.subprocess, "Popen", return_value=FakePopen(b"[]"),
            ) as launch, mock.patch.object(engine.processes, "cleanup_child"):
                self.assertEqual(shutil.which("codex"), str(alias))
                engine.enumerate_mcp_servers(root, 10)
                engine.offline_catalog_preflight(root, "demo", "Demo.", root / "SKILL.md", [], 10)
                engine.run_codex_query(root, "synthetic query", "low", "gpt-5.6-sol", 10, [])
                self.assertEqual(execute.call_count, 2)
                self.assertEqual(launch.call_count, 1)
                for call in [*execute.call_args_list, *launch.call_args_list]:
                    self.assertEqual(call.args[0][0], str(native))
                    self.assertEqual(call.kwargs["executable"], str(native))
                    self.assertEqual(call.kwargs["env"]["PATH"], str(alias.parent))
                self.assertEqual(os.environ["PATH"], str(alias.parent))

    def test_codex_external_tool_isolation(self) -> None:
        engine = import_script(CODEX_ENGINE, "layer2_codex_external_isolation")
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            servers = [{"name": "fixture-server"}, {"name": "server.with.dots"}]
            with mock.patch.object(
                engine.subprocess, "run",
                return_value=subprocess.CompletedProcess([], 0, json.dumps(servers).encode(), b""),
            ) as probe:
                names = engine.enumerate_mcp_servers(workspace, 10)
            self.assertEqual(names, ("fixture-server", "server.with.dots"))
            self.assertIn("mcp", probe.call_args.args[0])
            self.assertIn("list", probe.call_args.args[0])
            self.assertEqual(probe.call_args.kwargs["executable"], shutil.which("codex", path=str(Path(probe.call_args.args[0][0]).parent)))
            args = engine.skill_isolation_args((), names)
            for feature in ("apps", "browser_use", "computer_use", "hooks", "plugins", "skill_mcp_dependency_install"):
                self.assertIn(["--disable", feature], [args[i:i + 2] for i in range(len(args) - 1)])
            server_table = tomllib.loads(next(arg for arg in args if arg.startswith("mcp_servers=")))["mcp_servers"]
            self.assertEqual(set(server_table), set(names))
            for name in names:
                self.assertEqual(server_table[name], {
                    "enabled": False, "command": sys.executable, "args": ["-c", "raise SystemExit(1)"],
                })
            diagnostic_args = engine.skill_isolation_args((), names, ignore_user_config=False)
            diagnostic_table = tomllib.loads(next(arg for arg in diagnostic_args if arg.startswith("mcp_servers=")))["mcp_servers"]
            self.assertEqual(diagnostic_table, {name: {"enabled": False} for name in names})
            self.assertIn('web_search="disabled"', args)
            policy = engine.fixture_permission_args(workspace)
            self.assertNotIn("--sandbox", policy)
            self.assertIn('default_permissions="trigger-fixture"', policy)
            self.assertIn('permissions.trigger-fixture.network.enabled=false', policy)
            self.assertIn('approval_policy="never"', policy)
            self.assertIn(
                'permissions.trigger-fixture.filesystem={":root"="deny",":minimal"="read",'
                + json.dumps(str(workspace)) + '="read"}', policy,
            )
            for payload in (b"not-json", b"{}", b"[{}]", b'[{"name":""}]', b'[{"name":"duplicate"},{"name":"duplicate"}]'):
                with self.subTest(payload=payload), mock.patch.object(
                    engine.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, payload, b""),
                ), self.assertRaises(ValueError):
                    engine.enumerate_mcp_servers(workspace, 10)
            with mock.patch.dict(os.environ, {"UNRELATED_TOKEN": "never-inherit"}, clear=False):
                self.assertNotIn("UNRELATED_TOKEN", engine.codex_environment())

        marker = "CODEX_SKILL_SELECTED:demo-eval-fixed"
        witnesses = codex_witness("demo-eval", marker)
        base = [json.loads(line) for line in codex_stream(
            witnesses, selected_skill="demo-eval",
        ).splitlines()]
        for phase, item_type in (
            ("item.started", "mcp_tool_call"),
            ("item.completed", "mcp_tool_call"),
            ("item.updated", "web_search"),
            ("item.completed", "dynamic_tool_call"),
            ("item.started", "future_unknown_tool"),
        ):
            with self.subTest(phase=phase, item_type=item_type):
                event = {"type": phase, "item": {"type": item_type, "status": "failed", "result": None,
                         "error": {"message": "approval policy never denied this call"}}}
                parsed = engine.inspect_codex_jsonl(
                    "\n".join(map(json.dumps, [*base[:2], event, *base[2:]])),
                    "demo-eval", witnesses,
                )
                self.assertFalse(parsed["valid"])
                self.assertTrue(parsed["isolation_stop"])
        unavailable = {"type": "item.completed", "item": {"type": "error", "message": "tool unavailable"}}
        denied = engine.inspect_codex_jsonl(
            "\n".join(map(json.dumps, [*base[:2], unavailable, *base[2:]])),
            "demo-eval", witnesses,
        )
        self.assertFalse(denied["valid"])
        self.assertFalse(denied.get("isolation_stop", False))
        local = {"type": "item.completed", "item": {
            "id": "arbitrary", "type": "command_execution", "command": "pwd",
            "status": "completed", "exit_code": 0, "aggregated_output": "/tmp\n",
        }}
        self.assertFalse(engine.inspect_codex_jsonl(
            "\n".join(map(json.dumps, [*base[:2], local, *base[2:]])),
            "demo-eval", witnesses,
        )["valid"])
        for malformed in ({"type": []}, {"type": "item.started", "item": {"type": []}}):
            with self.subTest(malformed=malformed):
                parsed = engine.inspect_codex_jsonl(json.dumps(malformed), "demo-eval", witnesses)
                self.assertFalse(parsed["valid"])
                self.assertTrue(parsed["isolation_stop"])

    def test_codex_compound_body_read_requires_an_exact_leading_witness(self) -> None:
        engine = import_script(CODEX_ENGINE, "layer2_codex_compound_body_read")
        target_marker = "CODEX_SKILL_SELECTED:demo-eval-fixed"
        other_marker = "CODEX_SKILL_SELECTED:other-fixed"
        witnesses = {
            **codex_witness("demo-eval", target_marker),
            **codex_witness("other", other_marker),
        }
        base = [
            json.loads(line)
            for line in codex_stream(witnesses, selected_skill="demo-eval").splitlines()
        ]
        exact = engine.inspect_codex_jsonl(
            "\n".join(json.dumps(event) for event in base),
            "demo-eval",
            witnesses,
        )
        self.assertEqual(exact["read_witnesses"][0]["read_mode"], "exact-output")

        def with_command(command: str, output: str) -> list[dict[str, object]]:
            events = [dict(event) for event in base]
            for index in (2, 3):
                events[index] = {
                    **events[index],
                    "item": {**events[index]["item"], "command": command},
                }
            events[3]["item"]["aggregated_output"] = output
            return events

        target = witnesses["demo-eval"]
        other = witnesses["other"]
        leading_read = (
            f'/bin/zsh -c "sed -n \'1,240p\' {target["path"]} '
            "&& pwd && rg --files -g '!node_modules*' | head -200\""
        )
        body_then_metadata = target["body"] + "/tmp/fixture-workspace\n"
        accepted = inspect_codex_events(
            engine, with_command(leading_read, body_then_metadata), "demo-eval", witnesses,
        )
        self.assertTrue(accepted["valid"], accepted)
        self.assertTrue(accepted["selected"])
        self.assertEqual(accepted["consulted_skills"], ["demo-eval"])
        self.assertEqual(
            accepted["read_witnesses"][0]["read_mode"],
            "leading-compound-output",
        )

        invalid_cases = {
            "fabricated body with a path mention": (
                f'printf ignored {target["path"]}',
                body_then_metadata,
            ),
            "body read is not the first shell segment": (
                f'/bin/zsh -c "pwd && sed -n \'1,240p\' {target["path"]}"',
                "/tmp/fixture-workspace\n" + target["body"],
            ),
            "sed range is not the qualified form": (
                leading_read.replace("1,240p", "1,239p"),
                body_then_metadata,
            ),
            "output does not begin with the exact body": (
                leading_read,
                "prefix\n" + target["body"],
            ),
            "compound command reads a second staged body": (
                leading_read[:-1] + f' && cat {other["path"]}"',
                body_then_metadata + other["body"],
            ),
        }
        for label, (command, output) in invalid_cases.items():
            with self.subTest(label=label):
                parsed = inspect_codex_events(
                    engine, with_command(command, output), "demo-eval", witnesses,
                )
                self.assertFalse(parsed["valid"], parsed)
                self.assertIn("exact staged skill-body read", str(parsed["reason"]))
    def test_codex_started_body_read_requires_a_post_start_private_marker(self) -> None:
        engine = import_script(CODEX_ENGINE, "layer2_codex_started_body_read")
        marker = "CODEX_SKILL_SELECTED:demo-eval-0123456789abcdef0123456789abcdef"
        witnesses = codex_witness("demo-eval", marker)
        relative_path = witnesses["demo-eval"]["relative_path"]
        command = (
            f'/bin/zsh -c "sed -n \'1,240p\' {relative_path} '
            "&& printf '\\nFILES\\n' && ripwire . --for='find brief'\""
        )
        started = {"type": "item.started", "item": {
            "id": "read", "type": "command_execution", "command": command,
            "aggregated_output": "", "exit_code": None, "status": "in_progress",
        }}
        selected = {"type": "item.completed", "item": {
            "id": "message", "type": "agent_message", "text": marker,
        }}
        events = [
            {"type": "thread.started", "thread_id": "thread-1"},
            {"type": "turn.started"},
            {"type": "item.completed", "item": {
                "id": "progress", "type": "agent_message", "text": "Loading the matching skill.",
            }},
            started,
            selected,
            {"type": "turn.completed"},
        ]

        accepted = inspect_codex_events(engine, events, "demo-eval", witnesses)
        self.assertTrue(accepted["valid"], accepted)
        self.assertTrue(accepted["selected"])
        self.assertEqual(accepted["read_witnesses"][0]["read_mode"], "post-start-marker")
        self.assertIn("test_uuid = uuid.uuid4().hex\n", CODEX_ENGINE.read_text(encoding="utf-8"))

        invalid_cases = {
            "marker precedes read": [*events[:2], selected, started, events[-1]],
            "marker is absent": [*events[:4], {**selected, "item": {**selected["item"], "text": "No skill."}}, events[-1]],
            "command exposes marker": [*events[:3], {**started, "item": {**started["item"], "command": command[:-1] + f" && printf {marker}\\\""}}, *events[4:]],
            "read is not first": [*events[:3], {**started, "item": {**started["item"], "command": command.replace("sed -n", "pwd && sed -n")}}, *events[4:]],
            "two commands remain open": [*events[:4], {**started, "item": {**started["item"], "id": "second"}}, *events[4:]],
        }
        for label, malformed in invalid_cases.items():
            with self.subTest(label=label):
                self.assertFalse(
                    inspect_codex_events(engine, malformed, "demo-eval", witnesses)["valid"]
                )

    def test_codex_rejects_multiple_staged_body_reads(self) -> None:
        engine = import_script(CODEX_ENGINE, "layer2_codex_multiple_body_reads")
        witnesses = {
            **codex_witness("demo-eval", "CODEX_SKILL_SELECTED:demo-eval-fixed"),
            **codex_witness("other", "CODEX_SKILL_SELECTED:other-fixed"),
        }
        target = [json.loads(line) for line in codex_stream(
            witnesses, selected_skill="demo-eval",
        ).splitlines()]
        other = [json.loads(line) for line in codex_stream(
            witnesses, consulted_skill="other",
        ).splitlines()]
        parsed = inspect_codex_events(
            engine, [*target[:2], *other[2:4], *target[2:]], "demo-eval", witnesses,
        )
        self.assertFalse(parsed["valid"])
        self.assertIn("multiple staged skill bodies", str(parsed["reason"]))

    def test_codex_isolation_violation_retains_evidence_and_stops(self) -> None:
        engine = import_script(CODEX_ENGINE, "layer2_codex_isolation_stop")
        for item_type, expected_calls in (("mcp_tool_call", 1), ("error", 1)):
            with self.subTest(item_type=item_type), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = root / "SKILL.md"
                source.write_text("---\nname: demo\ndescription: Demo.\n---\nBody.\n", encoding="utf-8")
                corpus = root / "corpus.json"
                corpus.write_text(json.dumps([{"query": "first", "should_trigger": True},
                                              {"query": "second", "should_trigger": False}]), encoding="utf-8")
                workspace = root / "workspace"
                workspace.mkdir()
                evidence = root / "evidence"
                raw = "\n".join(map(json.dumps, [
                    {"type": "thread.started", "thread_id": "thread-1"},
                    {"type": "turn.started"},
                    {"type": "item.completed", "item": {"type": item_type, "message": "tool unavailable"}},
                    {"type": "item.completed", "item": {"type": "agent_message", "text": "Cannot use that tool."}},
                    {"type": "turn.completed"},
                ])).encode()
                with (
                    mock.patch.object(engine, "find_eval_file", return_value=corpus),
                    mock.patch.object(engine, "find_skill_source", return_value=source),
                    mock.patch.object(engine.shutil, "which", return_value="/usr/local/bin/codex"),
                    mock.patch.object(engine.tempfile, "mkdtemp", return_value=str(workspace)),
                    mock.patch.object(engine.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b"", b"")),
                    mock.patch.object(engine, "enumerate_non_target_skills", return_value=()),
                    mock.patch.object(engine, "enumerate_mcp_servers", return_value=()),
                    mock.patch.object(engine, "offline_catalog_preflight", return_value=({}, "ok")),
                    mock.patch.object(engine, "cli_preflight", return_value=({}, "ok")),
                    mock.patch.object(engine, "run_codex_query", return_value=(0, raw, b"", False)) as provider,
                    mock.patch.object(sys, "argv", [str(CODEX_ENGINE), "demo", "--runs", "1", "--evidence-dir", str(evidence)]),
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()),
                ):
                    self.assertEqual(engine.main(), 1)
                self.assertEqual(provider.call_count, expected_calls)
                self.assertEqual((evidence / "case-001-trial-01.jsonl").read_bytes(), raw)
                self.assertEqual((evidence / "isolation-stop.json").exists(), item_type == "mcp_tool_call")
                self.assertFalse(workspace.exists())

    def test_codex_contracts_remain_unchanged(self) -> None:
        codex = import_script(CODEX_RUNNER, "layer2_codex_wrapper")
        engine = import_script(CODEX_ENGINE, "layer2_codex_engine")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "SKILL.md"
            source.write_text("---\nname: demo\ndescription: Demo.\n---\n\nBody.\n", encoding="utf-8")
            workspace = root / "workspace"
            workspace.mkdir()
            auth_home = root / "codex-home"
            auth_home.mkdir()
            auth_file = auth_home / "auth.json"
            auth_file.write_text("credential sentinel\n", encoding="utf-8")
            marker = "CODEX_SKILL_SELECTED:demo-eval-fixed"
            with mock.patch.object(engine.shutil, "copy2") as credential_copy:
                staged = engine.stage_repository_skill(source, workspace, "demo-eval", marker)
            witnesses = engine.skill_witnesses(workspace, {"demo-eval": marker})
            read_command = f"cat {witnesses['demo-eval']['path']}"
            valid = "\n".join(
                [
                    json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
                    json.dumps({"type": "turn.started"}),
                    json.dumps({
                        "type": "item.started",
                        "item": {"id": "read-skill", "type": "command_execution", "command": read_command},
                    }),
                    json.dumps({
                        "type": "item.completed",
                        "item": {
                            "id": "read-skill", "type": "command_execution", "command": read_command,
                            "status": "completed", "exit_code": 0,
                            "aggregated_output": witnesses["demo-eval"]["body"],
                        },
                    }),
                    json.dumps(
                        {
                            "type": "item.started",
                            "item": {"type": "agent_message", "text": marker},
                        }
                    ),
                    json.dumps(
                        {
                            "type": "item.updated",
                            "item": {"type": "agent_message", "text": marker},
                        }
                    ),
                    json.dumps(
                        {
                            "type": "item.completed",
                            "item": {"type": "agent_message", "text": "Preparing to answer."},
                        }
                    ),
                    json.dumps(
                        {
                            "type": "item.completed",
                            "item": {"type": "agent_message", "text": f"{marker}\nDone."},
                        }
                    ),
                    json.dumps({"type": "turn.completed"}),
                ]
            ).encode("utf-8")
            parsed = engine.inspect_codex_jsonl(
                valid, "demo-eval", witnesses, requested_model="gpt-5.6-sol",
            )
            competing = engine.inspect_codex_jsonl(
                valid.replace(b"Done.", b"CODEX_SKILL_SELECTED:other-fixed"),
                "demo-eval", witnesses,
            )
            marker_not_first = engine.inspect_codex_jsonl(
                valid.replace(
                    f"{marker}\\nDone.".encode(),
                    f"Progress\\n{marker}".encode(),
                ),
                "demo-eval", witnesses,
            )
            missing_lifecycle = engine.inspect_codex_jsonl(
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"type": "agent_message", "text": marker},
                    }
                ),
                "demo-eval", witnesses,
            )
            wrong_order = engine.inspect_codex_jsonl(
                "\n".join(
                    [
                        json.dumps({"type": "turn.completed"}),
                        json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
                        json.dumps({"type": "turn.started"}),
                    ]
                ),
                "demo-eval", witnesses,
            )
            no_response = engine.inspect_codex_jsonl(
                "\n".join(
                    [
                        json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
                        json.dumps({"type": "turn.started"}),
                        json.dumps({"type": "turn.completed"}),
                    ]
                ),
                "demo-eval", witnesses,
            )
            top_error = engine.inspect_codex_jsonl(
                valid.replace(
                    b'{"type": "turn.completed"}',
                    b'{"type": "error"}\n{"type": "turn.completed"}',
                ),
                "demo-eval", witnesses,
            )
            item_error = engine.inspect_codex_jsonl(
                valid.replace(
                    b'{"type": "item.completed", "item": {"type": "agent_message", "text": "Preparing to answer."}}',
                    b'{"type": "item.completed", "item": {"type": "error", "message": "failed"}}',
                ),
                "demo-eval", witnesses,
            )
            completed_error_items = [
                engine.inspect_codex_jsonl(
                    valid.replace(
                        b'{"type": "item.completed", "item": {"type": "agent_message", "text": "Preparing to answer."}}',
                        json.dumps(
                            {
                                "type": "item.completed",
                                "item": {"type": "error", field: value},
                            }
                        ).encode("utf-8"),
                    ),
                    "demo-eval", witnesses,
                )
                for field, value in (
                    ("message", "failed"),
                    ("error", "budget warning"),
                    ("status", "failed"),
                )
            ]
            domain_payload = engine.inspect_codex_jsonl(
                valid.replace(
                    b'"text": "Preparing to answer."',
                    b'"text": "Preparing to answer.", "error": {"kind": "domain-data"}',
                ),
                "demo-eval", witnesses,
            )
            evidence_dir = root / "evidence"
            evidence_dir.mkdir()
            evidence = engine.retain_run_evidence(evidence_dir, 1, 1, valid, b"stderr\r\n")
            invalid_utf8 = b'{"type":"thread.started"}\r\n\xff'
            invalid_evidence_dir = root / "invalid-evidence"
            invalid_evidence_dir.mkdir()
            invalid_evidence = engine.retain_run_evidence(
                invalid_evidence_dir,
                1,
                1,
                invalid_utf8,
                b"stderr\xff",
            )
            invalid_utf8_result = engine.inspect_codex_jsonl(invalid_utf8, "demo-eval", witnesses)

            residue = root / "residue"
            residue.mkdir()
            with mock.patch.object(engine.shutil, "rmtree", return_value=None):
                cleanup_residue = engine.remove_workspace(residue)

            invalid_corpus_paths: list[Path] = []
            unreadable = root / "unreadable-corpus"
            unreadable.mkdir()
            invalid_corpus_paths.append(unreadable)
            for name, body in (
                ("malformed", "{"),
                ("non-list", "{}"),
                ("empty", "[]"),
                ("invalid-case", '[{"query":"q"}]'),
                (
                    "duplicate",
                    '[{"query":"q","should_trigger":true},{"query":"q","should_trigger":false}]',
                ),
            ):
                path = root / f"{name}.json"
                path.write_text(body, encoding="utf-8")
                invalid_corpus_paths.append(path)
            invalid_corpus_messages: list[str] = []
            invalid_corpus_subprocess_calls = 0
            for path in invalid_corpus_paths:
                with (
                    mock.patch.object(engine, "find_eval_file", return_value=path),
                    mock.patch.object(engine, "find_skill_source", return_value=source),
                    mock.patch.object(engine.subprocess, "run") as invalid_run,
                    mock.patch.object(sys, "argv", [str(CODEX_ENGINE), "demo"]),
                    self.assertRaises(SystemExit) as invalid_exit,
                ):
                    engine.main()
                invalid_corpus_subprocess_calls += invalid_run.call_count
                invalid_corpus_messages.append(str(invalid_exit.exception))

            agents_skills = root / "home" / ".agents" / "skills"
            legacy_skills = auth_home / "skills"
            for skill_root, skill_name in (
                (agents_skills, "user-skill"),
                (legacy_skills, "legacy-skill"),
            ):
                skill_file = skill_root / skill_name / "SKILL.md"
                skill_file.parent.mkdir(parents=True)
                skill_file.write_text(
                    f"---\nname: {skill_name}\ndescription: {skill_name}.\n---\n",
                    encoding="utf-8",
                )
            with mock.patch.object(
                engine,
                "skill_source_roots",
                return_value=(agents_skills, legacy_skills, root / "missing-admin-skills"),
            ):
                disabled_skills = engine.enumerate_non_target_skills(staged / "SKILL.md")
            isolation_args = engine.skill_isolation_args(disabled_skills)

            invalid_skill_root = root / "invalid-skill-root"
            invalid_skill_root.write_text("not a directory\n", encoding="utf-8")
            with (
                mock.patch.object(engine, "skill_source_roots", return_value=(invalid_skill_root,)),
                self.assertRaisesRegex(ValueError, "not a directory"),
            ):
                engine.enumerate_non_target_skills(staged / "SKILL.md")
            with (
                mock.patch.dict(os.environ, {"CODEX_HOME": "relative-codex-home"}, clear=False),
                self.assertRaisesRegex(ValueError, "must be absolute"),
            ):
                engine.skill_source_roots()

            catalog_text = "\n".join(
                [
                    "## Skills",
                    "### Available skills",
                    f"- demo-eval: Demo. (file: {(staged / 'SKILL.md').resolve()})",
                    "### How to use skills",
                    "- Follow the selected skill.",
                ]
            )
            prompt_output = json.dumps(
                [{"role": "developer", "content": [{"type": "input_text", "text": catalog_text}]}]
            ).encode("utf-8")
            catalog_readiness, catalog_reason = engine.inspect_catalog_prompt(
                prompt_output,
                "demo-eval",
                "Demo.",
                staged / "SKILL.md",
                workspace,
            )
            relative_catalog_text = catalog_text.replace(
                "### Available skills",
                f"### Skill roots\n- `r0` = `{workspace / '.agents' / 'skills'}`\n### Available skills",
            ).replace(
                str((staged / "SKILL.md").resolve()),
                "r0/demo-eval/SKILL.md",
            )
            relative_prompt_output = json.dumps([{"text": relative_catalog_text}]).encode("utf-8")
            relative_catalog_readiness, relative_catalog_reason = engine.inspect_catalog_prompt(
                relative_prompt_output,
                "demo-eval",
                "Demo.",
                staged / "SKILL.md",
                workspace,
            )
            shortened_readiness, shortened_reason = engine.inspect_catalog_prompt(
                json.dumps(
                    [
                        {
                            "text": catalog_text
                            + "\nSkill descriptions were shortened to fit the skills context budget."
                        }
                    ]
                ).encode("utf-8"),
                "demo-eval",
                "Demo.",
                staged / "SKILL.md",
                workspace,
            )
            extra_readiness, extra_reason = engine.inspect_catalog_prompt(
                json.dumps(
                    [
                        {
                            "text": catalog_text.replace(
                                "### How to use skills",
                                "- other: Other. (file: /tmp/other/SKILL.md)\n### How to use skills",
                            )
                        }
                    ]
                ).encode("utf-8"),
                "demo-eval",
                "Demo.",
                staged / "SKILL.md",
                workspace,
            )

            wrong_skill = root / "wrong-skill" / "SKILL.md"
            wrong_skill.parent.mkdir()
            wrong_skill.write_text("---\nname: demo-eval\ndescription: Demo.\n---\n", encoding="utf-8")
            wrong_path_output = prompt_output.replace(
                str((staged / "SKILL.md").resolve()).encode("utf-8"),
                str(wrong_skill.resolve()).encode("utf-8"),
            )
            wrong_path_readiness, wrong_path_reason = engine.inspect_catalog_prompt(
                wrong_path_output,
                "demo-eval",
                "Demo.",
                staged / "SKILL.md",
                workspace,
            )
            missing_path_readiness, missing_path_reason = engine.inspect_catalog_prompt(
                prompt_output.replace(
                    str((staged / "SKILL.md").resolve()).encode("utf-8"),
                    str(root / "missing-skill" / "SKILL.md").encode("utf-8"),
                ),
                "demo-eval",
                "Demo.",
                staged / "SKILL.md",
                workspace,
            )
            malformed_path_readiness, malformed_path_reason = engine.inspect_catalog_prompt(
                prompt_output.replace(
                    str((staged / "SKILL.md").resolve()).encode("utf-8"),
                    b"relative/SKILL.md",
                ),
                "demo-eval",
                "Demo.",
                staged / "SKILL.md",
                workspace,
            )
            missing_identity_readiness, missing_identity_reason = engine.inspect_catalog_prompt(
                prompt_output.replace(
                    f" (file: {(staged / 'SKILL.md').resolve()})".encode("utf-8"),
                    b"",
                ),
                "demo-eval",
                "Demo.",
                staged / "SKILL.md",
                workspace,
            )

            preflight_captured: dict[str, object] = {}

            def fake_preflight_run(
                command: list[str],
                **kwargs: object,
            ) -> subprocess.CompletedProcess[bytes]:
                preflight_captured["command"] = command
                preflight_captured["kwargs"] = kwargs
                return subprocess.CompletedProcess(command, 0, prompt_output, b"local warning")

            with (
                mock.patch.dict(os.environ, {"CODEX_HOME": str(auth_home)}, clear=False),
                mock.patch.object(engine.subprocess, "run", side_effect=fake_preflight_run),
            ):
                offline_readiness, offline_reason = engine.offline_catalog_preflight(
                    workspace,
                    "demo-eval",
                    "Demo.",
                    staged / "SKILL.md",
                    isolation_args,
                    30,
                )
            probe_failures = []
            for failure in (
                subprocess.TimeoutExpired(["codex"], 30),
                OSError("unavailable"),
                subprocess.CompletedProcess([], 2, b"", b"failure"),
                subprocess.CompletedProcess([], 0, b"not-json", b""),
            ):
                with mock.patch.object(
                    engine.subprocess,
                    "run",
                    side_effect=failure if isinstance(failure, BaseException) else None,
                    return_value=None if isinstance(failure, BaseException) else failure,
                ):
                    probe_failures.append(
                        engine.offline_catalog_preflight(
                            workspace,
                            "demo-eval",
                            "Demo.",
                            staged / "SKILL.md",
                            isolation_args,
                            30,
                        )
                    )

            captured: dict[str, object] = {}

            def fake_run(command: list[str], **kwargs: object) -> FakePopen:
                captured["command"] = command
                captured["kwargs"] = kwargs
                return FakePopen(valid)

            launch_evidence: dict[str, object] = {}
            with (
                mock.patch.dict(os.environ, {"CODEX_HOME": str(auth_home)}, clear=False),
                mock.patch.object(engine.subprocess, "Popen", side_effect=fake_run),
                mock.patch.object(engine.processes, "cleanup_child"),
            ):
                rc, stdout, stderr, timed_out = engine.run_codex_query(
                    workspace,
                    "query",
                    "low",
                    "gpt-5.6-sol",
                    30,
                    isolation_args,
                    process_evidence=launch_evidence,
                )

            timeout_stdout = b"partial-jsonl\r\n"
            timeout_stderr = b"partial-stderr\r\n"
            timeout_evidence_dir = root / "timeout-evidence"
            timeout_evidence_dir.mkdir()
            timeout_child = FakePopen(timeout_stdout, timeout_stderr)
            timeout_child.timeout = True
            with mock.patch.object(
                engine.subprocess,
                "Popen", return_value=timeout_child,
            ), mock.patch.object(engine.processes, "cleanup_child"):
                timeout_rc, retained_timeout_stdout, retained_timeout_stderr, timeout_timed_out = (
                    engine.run_codex_query(
                        workspace,
                        "query that times out",
                        "low",
                        "gpt-5.6-sol",
                        7,
                        isolation_args,
                    )
                )
            timeout_evidence = engine.retain_run_evidence(
                timeout_evidence_dir,
                1,
                2,
                retained_timeout_stdout,
                retained_timeout_stderr,
            )
            with mock.patch.object(
                engine.subprocess,
                "Popen", return_value=FakePopen(b"signal-output", b"signal-stderr", -1),
            ), mock.patch.object(engine.processes, "cleanup_child"):
                signal_rc, signal_stdout, signal_stderr, signal_timed_out = (
                    engine.run_codex_query(
                        workspace,
                        "query interrupted by signal",
                        "low",
                        "gpt-5.6-sol",
                        7,
                        isolation_args,
                    )
                )

            main_corpus = root / "main-codex-corpus.json"
            main_corpus.write_text(
                json.dumps([{"query": "q", "should_trigger": True}]) + "\n",
                encoding="utf-8",
            )
            main_isolation_failures = []
            for case_index, failure_kind in enumerate(("preflight", "roots-changed"), start=1):
                main_workspace = root / f"main-workspace-{case_index}"
                main_evidence = root / f"main-codex-evidence-{case_index}"
                main_stdout = io.StringIO()
                main_stderr = io.StringIO()
                enumerated = (
                    [disabled_skills]
                    if failure_kind == "preflight"
                    else [disabled_skills, (*disabled_skills, root / "new-skill" / "SKILL.md")]
                )
                preflight_result = (
                    (None, "catalog proof rejected")
                    if failure_kind == "preflight"
                    else (catalog_readiness, "Codex catalog preflight passed")
                )
                with (
                    mock.patch.object(engine, "find_eval_file", return_value=main_corpus),
                    mock.patch.object(engine, "find_skill_source", return_value=source),
                    mock.patch.object(engine.shutil, "which", return_value="/usr/local/bin/codex"),
                    mock.patch.object(
                        engine.subprocess,
                        "run",
                        return_value=subprocess.CompletedProcess([], 0, b"", b""),
                    ),
                    mock.patch.object(
                        engine,
                        "enumerate_non_target_skills",
                        side_effect=enumerated,
                    ) as main_enumerate,
                    mock.patch.object(engine, "enumerate_mcp_servers", return_value=()),
                    mock.patch.object(
                        engine,
                        "offline_catalog_preflight",
                        return_value=preflight_result,
                    ) as main_preflight,
                    mock.patch.object(engine, "cli_preflight", return_value=({}, "ok")),
                    mock.patch.object(engine, "run_codex_query") as rejected_provider,
                    mock.patch.object(
                        engine.uuid,
                        "uuid4",
                        return_value=SimpleNamespace(hex=f"{case_index:08d}"),
                    ),
                    mock.patch.object(engine.tempfile, "mkdtemp", return_value=str(main_workspace)),
                    mock.patch.object(
                        sys,
                        "argv",
                        [
                            str(CODEX_ENGINE),
                            "demo",
                            "--runs",
                            "1",
                            "--evidence-dir",
                            str(main_evidence),
                        ],
                    ),
                    contextlib.redirect_stdout(main_stdout),
                    contextlib.redirect_stderr(main_stderr),
                ):
                    main_exit = engine.main()
                main_isolation_failures.append(
                    (
                        failure_kind,
                        main_exit,
                        main_stdout.getvalue(),
                        main_stderr.getvalue(),
                        main_workspace.exists(),
                        sorted(main_evidence.iterdir()),
                        main_enumerate.call_count,
                        main_preflight.call_args,
                        rejected_provider.call_count,
                        main_workspace
                        / ".agents"
                        / "skills"
                        / f"demo-eval-{case_index:08d}"
                        / "SKILL.md",
                    )
                )

            fixture_root = root / "fixture"
            plugin_root = fixture_root / "speckit-pro"
            (plugin_root / "codex-skills" / "demo").mkdir(parents=True)
            codex_eval = fixture_root / "tests/speckit-pro/layer2-trigger/codex-evals/demo-trigger.json"
            codex_eval.parent.mkdir(parents=True)
            codex_eval.write_text("{}\n", encoding="utf-8")
            codex.PLUGIN_ROOT = plugin_root

            with (
                mock.patch.object(codex.shutil, "which", return_value=str(root / "codex")) as which_codex,
                mock.patch.object(codex.os, "execv", side_effect=RuntimeError("intercept")) as execv,
                self.assertRaisesRegex(RuntimeError, "intercept"),
            ):
                codex.main(["demo", "--run", "--profile", "fast", "--run", "tail"])
            delegated_executable, delegated_argv = execv.call_args.args

            with mock.patch.object(
                engine.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(
                    [], 0, f"{engine.PINNED_CODEX_VERSION}\n".encode("utf-8"), b"",
                ),
            ):
                qualified_codex_preflight = engine.cli_preflight()
            with mock.patch.object(
                engine.subprocess,
                "run",
                return_value=subprocess.CompletedProcess([], 0, b"codex-cli 0.0.0\n", b""),
            ):
                rejected_codex_preflight = engine.cli_preflight()

            checks = {
                "imports Codex wrapper": codex is not None,
                "all runners avoid shell execution": not any(
                    calls_forbidden_process_api(path)
                    for path in (CLAUDE_RUNNER, CODEX_RUNNER, CODEX_ENGINE)
                ),
                "Layer-2 command vectors avoid hard-coded python3": not any(
                    has_hardcoded_python3_command(path)
                    for path in (CLAUDE_RUNNER, CODEX_RUNNER, CODEX_ENGINE)
                ),
                "Codex --run checks the executable": which_codex.call_args_list == [mock.call("codex")],
                "Codex --run delegates through the current Python": delegated_executable == sys.executable
                and delegated_argv[:2] == [sys.executable, str(LAYER2 / "run_codex_evals.py")],
                "Codex --run strips control flags and preserves arguments": "--run" not in delegated_argv
                and delegated_argv[2:] == ["demo", "--profile", "fast", "tail"],
                "Codex default effort remains low": engine.DEFAULT_REASONING_EFFORT == "low",
                "Codex default model remains approved": engine.DEFAULT_MODEL == "gpt-5.6-sol",
                "Codex preflight pins the qualified CLI build": qualified_codex_preflight[0] is not None
                and qualified_codex_preflight[0]["version"] == engine.PINNED_CODEX_VERSION
                and qualified_codex_preflight[0]["request_max_retries"] == 0
                and qualified_codex_preflight[0]["stream_max_retries"] == 0
                and rejected_codex_preflight[0] is None,
                "Codex skill remains repository scoped": staged == workspace / ".agents" / "skills" / "demo-eval",
                "Codex source description parser preserves the staged routing description": engine.source_skill_description(
                    staged / "SKILL.md"
                )
                == "Demo.",
                "Codex isolation deny list is fresh canonical and excludes only the target": disabled_skills
                == tuple(
                    sorted(
                        (
                            (agents_skills / "user-skill" / "SKILL.md").resolve(),
                            (legacy_skills / "legacy-skill" / "SKILL.md").resolve(),
                        ),
                        key=str,
                    )
                )
                and (staged / "SKILL.md").resolve() not in disabled_skills,
                "Codex isolation uses only process-local negative skill controls": isolation_args[:4]
                == ["--disable", "plugins", "-c", "skills.bundled.enabled=false"]
                and isolation_args[4] == "-c"
                and isolation_args[5].startswith("skills.config=[")
                and all(f"path={json.dumps(str(path))},enabled=false" in isolation_args[5] for path in disabled_skills)
                and "enabled=true" not in isolation_args[5]
                and "max_context_tokens" not in " ".join(isolation_args),
                "Codex staging never copies credentials": credential_copy.call_count == 0
                and auth_file.read_text(encoding="utf-8") == "credential sentinel\n"
                and "auth.json" not in CODEX_ENGINE.read_text(encoding="utf-8"),
                "Codex exact marker remains selected": parsed["valid"] and parsed["selected"],
                "Codex competing marker remains invalid": not competing["valid"],
                "Codex marker must lead its completed message": not marker_not_first["valid"]
                and "not first" in str(marker_not_first["reason"]),
                "Codex lifecycle requires one ordered completed turn": not missing_lifecycle["valid"]
                and "lifecycle" in str(missing_lifecycle["reason"])
                and not wrong_order["valid"]
                and "out of order" in str(wrong_order["reason"])
                and not no_response["valid"]
                and "response" in str(no_response["reason"]),
                "Codex ignores started copies and permits prior completed progress": parsed["valid"]
                and parsed["selected_marker"] == marker,
                "Codex provider errors fail without confusing domain payloads": not top_error["valid"]
                and not item_error["valid"]
                and all(not result["valid"] for result in completed_error_items)
                and domain_payload["valid"],
                "Codex catalog proof requires one exact unshortened target": catalog_readiness is not None
                and catalog_reason == "Codex catalog preflight passed"
                and catalog_readiness["catalog_skill_entries"] == 1
                and catalog_readiness["target_entries"] == 1
                and catalog_readiness["target_description_exact"] is True
                and catalog_readiness["rendered_file_valid"] is True
                and catalog_readiness["target_file_exact"] is True
                and catalog_readiness["warning_present"] is False
                and catalog_readiness["other_skill_entries"] == 0
                and catalog_readiness["proof_scope"]
                == "catalog-only; debug prompt-input loads user config",
                "Codex catalog proof canonicalizes the CLI relative file identity": relative_catalog_readiness
                is not None
                and relative_catalog_reason == "Codex catalog preflight passed"
                and relative_catalog_readiness["root_alias_valid"] is True
                and relative_catalog_readiness["target_file_exact"] is True,
                "Codex catalog proof rejects shortening warnings and extra entries": shortened_readiness is None
                and "warning_present" in shortened_reason
                and extra_readiness is None
                and "catalog_skill_entries" in extra_reason,
                "Codex catalog proof rejects same-name same-description wrong or invalid file identity": wrong_path_readiness
                is None
                and "target_file_exact" in wrong_path_reason
                and missing_path_readiness is None
                and "rendered_file_valid" in missing_path_reason
                and malformed_path_readiness is None
                and "rendered_file_valid" in malformed_path_reason
                and missing_identity_readiness is None
                and "rendered_file_valid" in missing_identity_reason,
                "Codex offline probe preserves matched isolation overrides without claiming exec equivalence": preflight_captured[
                    "command"
                ]
                == [engine.codex_executable(), "debug", "prompt-input",
                    *engine.fixture_permission_args(workspace), *isolation_args]
                and "--ignore-user-config" not in preflight_captured["command"]
                and preflight_captured["kwargs"]["cwd"] == workspace
                and preflight_captured["kwargs"]["env"].get("CODEX_HOME") == str(auth_home)
                and preflight_captured["kwargs"]["shell"] is False
                and preflight_captured["kwargs"]["executable"] == shutil.which("codex", path=str(Path(preflight_captured["command"][0]).parent))
                and offline_readiness == catalog_readiness
                and offline_reason == "Codex catalog preflight passed",
                "Codex offline probe errors all fail closed without rendered-prompt evidence": all(
                    readiness is None and reason.startswith("Codex catalog preflight")
                    for readiness, reason in probe_failures
                ),
                "Codex requested and unresolved model remain distinct": parsed["requested_model"] == "gpt-5.6-sol"
                and parsed["resolved_model"] is None,
                "Codex raw streams remain exact": Path(evidence["jsonl_path"]).read_bytes() == valid
                and Path(evidence["stderr_path"]).read_bytes() == b"stderr\r\n",
                "Codex raw hashes remain exact": evidence["jsonl_sha256"] == hashlib.sha256(valid).hexdigest()
                and evidence["stderr_sha256"] == hashlib.sha256(b"stderr\r\n").hexdigest(),
                "Codex retains undecodable bytes before rejecting semantics": not invalid_utf8_result["valid"]
                and Path(invalid_evidence["jsonl_path"]).read_bytes() == invalid_utf8
                and invalid_evidence["jsonl_sha256"] == hashlib.sha256(invalid_utf8).hexdigest(),
                "Codex cleanup reports disposable residue": cleanup_residue is not None,
                "Codex rejects invalid corpora before subprocess": invalid_corpus_subprocess_calls == 0
                and len(invalid_corpus_messages) == len(invalid_corpus_paths)
                and any("at least one" in message for message in invalid_corpus_messages)
                and any("duplicates" in message for message in invalid_corpus_messages),
                "Codex direct result remains binary": (rc, stdout, stderr, timed_out)
                == (0, valid, b"", False),
                "Codex execution receives the exact proved isolation overrides": captured["command"][
                    -len(isolation_args) - 1 :
                ]
                == [*isolation_args, "query"],
                "Codex launch freezes provider retries and identity scope": launch_evidence["launch_contract"]
                == {
                    "config_isolated": True,
                    "retries_disabled": True,
                    "requested_model": "gpt-5.6-sol",
                    "reasoning_effort": "low",
                    "model_provider": engine.MODEL_PROVIDER_ID,
                    "model_identity_evidence": "request-only",
                    "stdin_prompt_isolated": True,
                    "stdin_mode": "pseudo-terminal" if os.name != "nt" else "null-device",
                },
                "Codex timeout retains partial raw streams and hashes": timeout_rc == -1
                and timeout_timed_out
                and retained_timeout_stdout == timeout_stdout
                and retained_timeout_stderr == timeout_stderr
                and Path(timeout_evidence["jsonl_path"]).read_bytes() == timeout_stdout
                and Path(timeout_evidence["stderr_path"]).read_bytes() == timeout_stderr
                and timeout_evidence["jsonl_sha256"] == hashlib.sha256(timeout_stdout).hexdigest()
                and timeout_evidence["stderr_sha256"] == hashlib.sha256(timeout_stderr).hexdigest(),
                "Codex timeout invalidates a negative case": not engine.case_passes(
                    False,
                    triggers=0,
                    runs=3,
                    threshold=0.5,
                    invalid_runs=int(timeout_timed_out),
                ),
                "Codex signal exit remains distinct from timeout": signal_rc == -1
                and not signal_timed_out
                and signal_stdout == b"signal-output"
                and signal_stderr == b"signal-stderr",
                "Codex retains existing login environment": captured["kwargs"]["env"].get("CODEX_HOME")
                == str(auth_home)
                and captured["kwargs"]["env"].get("HOME") == os.environ.get("HOME"),
                "Codex executable override retains statically verified provenance": captured["kwargs"]["executable"]
                == shutil.which("codex", path=str(Path(captured["command"][0]).parent)),
                "Codex keeps least privilege flags": "--sandbox" not in captured["command"]
                and 'default_permissions="trigger-fixture"' in captured["command"]
                and "permissions.trigger-fixture.network.enabled=false" in captured["command"]
                and 'approval_policy="never"' in captured["command"]
                and "--strict-config" in captured["command"]
                and "--ephemeral" in captured["command"]
                and "--ignore-user-config" in captured["command"]
                and "--json" in captured["command"]
                and "--disable" in captured["command"]
                and captured["command"][captured["command"].index("--disable") + 1] == "plugins"
                and "skills.bundled.enabled=false" in captured["command"]
                and captured["command"][captured["command"].index("-m") + 1] == "gpt-5.6-sol"
                and 'model_reasoning_effort="low"' in captured["command"]
                and f"model_providers.{engine.MODEL_PROVIDER_ID}.request_max_retries=0" in captured["command"]
                and f"model_providers.{engine.MODEL_PROVIDER_ID}.stream_max_retries=0" in captured["command"]
                and "unbounded_connection_retries" in captured["command"],
                "Codex keeps rules and approval boundaries enabled": "--ignore-rules" not in captured["command"]
                and "--dangerously-bypass-approvals-and-sandbox" not in captured["command"]
                and "--full-auto" not in captured["command"],
                "Codex negative transport remains fail closed": not engine.case_passes(
                    False, triggers=0, runs=3, threshold=0.5, invalid_runs=1
                ),
                "Codex rejects catalog or root drift before provider launch and cleans workspace": all(
                    exit_code == 1
                    and stdout == ""
                    and "ERROR:" in stderr
                    and not workspace_exists
                    and [path.name for path in evidence_files] == ["arm-cleanup.json"]
                    and provider_calls == 0
                    and preflight_call is not None
                    and preflight_call.args[3] == expected_target_skill
                    and preflight_call.args[4] == engine.skill_isolation_args(disabled_skills)
                    and enumerate_calls == (1 if failure_kind == "preflight" else 2)
                    for (
                        failure_kind,
                        exit_code,
                        stdout,
                        stderr,
                        workspace_exists,
                        evidence_files,
                        enumerate_calls,
                        preflight_call,
                        provider_calls,
                        expected_target_skill,
                    ) in main_isolation_failures
                ),
            }
            for name, condition in checks.items():
                with self.subTest(msg=name):
                    self.assertTrue(condition)

    def test_claude_sibling_catalog_scores_sibling_selection_as_non_selection(self) -> None:
        claude = import_script(CLAUDE_RUNNER, "layer2_claude_siblings")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skills = root / "skills"
            for name, description in (("demo", "Demo target."), ("other", "Other sibling."), ("third", "Third sibling.")):
                (skills / name).mkdir(parents=True)
                (skills / name / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: {description}\n---\n\nBody of {name} must not copy.\n",
                    encoding="utf-8",
                )
            plugin_root = root / "staged-plugin"
            plugin = "skill-catalog-eval-fixed"
            nonce = "CLAUDE_SKILL_SELECTED_fixed"
            siblings = {"other": skills / "other" / "SKILL.md", "third": skills / "third" / "SKILL.md"}
            _staged, target = claude.stage_measurement_plugin(
                skills / "demo" / "SKILL.md", plugin_root, plugin, "demo-eval-fixed", nonce, siblings
            )
            other_text = (plugin_root / "skills" / "other" / "SKILL.md").read_text(encoding="utf-8")
            no_speckit_text = (
                plugin_root / "skills" / "no-speckit-skill" / "SKILL.md"
            ).read_text(encoding="utf-8")
            target_text = (plugin_root / "skills" / "demo-eval-fixed" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("description: Other sibling.", other_text)
            self.assertNotIn(nonce, other_text)
            self.assertNotIn("must not copy", other_text)
            assert_no_speckit_contracts(self, claude, no_speckit_text)
            self.assertIn("say so in one line and stop.", no_speckit_text)
            self.assertIn(claude.MEASUREMENT_STUB_SENTENCE, target_text)
            with self.assertRaisesRegex(ValueError, "collides"):
                claude.stage_measurement_plugin(
                    skills / "demo" / "SKILL.md", root / "collision", plugin, "demo-eval-fixed", nonce,
                    {"demo-eval-fixed": skills / "other" / "SKILL.md"},
                )

            sibling_ids = frozenset(
                {f"{plugin}:no-speckit-skill", f"{plugin}:other", f"{plugin}:third"}
            )
            raw = claude_stream(plugin_root, plugin, target, nonce)
            events = [json.loads(line) for line in raw.splitlines()]
            events[0]["skills"] = [target, *sorted(sibling_ids)]

            def parse(mutated: list[dict[str, object]], known: frozenset[str] = sibling_ids) -> dict[str, object]:
                return claude.inspect_claude_stream(
                    "\n".join(json.dumps(event) for event in mutated), plugin, plugin_root, target, nonce,
                    "sonnet", known,
                )

            target_selected = parse(events)
            self.assertTrue(target_selected["valid"] and target_selected["selected"])
            self.assertEqual(target_selected["sibling_selections"], [])

            sibling = json.loads(json.dumps(events))
            sibling[1]["message"]["content"][0]["input"]["skill"] = f"{plugin}:other"
            sibling[3]["message"]["content"][0]["text"] = "Selected the other sibling."
            sibling_selected = parse(sibling)
            self.assertTrue(sibling_selected["valid"])
            self.assertFalse(sibling_selected["selected"])
            self.assertEqual(sibling_selected["sibling_selections"], [f"{plugin}:other"])
            self.assertEqual(sibling_selected["reason"], "sibling Skill selection")

            no_speckit = json.loads(json.dumps(events))
            no_speckit[1]["message"]["content"][0]["input"]["skill"] = f"{plugin}:no-speckit-skill"
            no_speckit[3]["message"]["content"][0]["text"] = "No SpecKit skill applies."
            no_speckit_selected = parse(no_speckit)
            self.assertTrue(no_speckit_selected["valid"])
            self.assertFalse(no_speckit_selected["selected"])
            self.assertEqual(no_speckit_selected["sibling_selections"], [f"{plugin}:no-speckit-skill"])

            self.assertFalse(parse(sibling, frozenset())["valid"], "an undeclared sibling stays a competing selection")
            bare_target = json.loads(json.dumps(events))
            bare_target[1]["message"]["content"][0]["input"]["skill"] = "demo-eval-fixed"
            bare_selected = parse(bare_target)
            self.assertTrue(bare_selected["valid"] and bare_selected["selected"], "the host resolves the bare name to the staged skill")
            bare_sibling = json.loads(json.dumps(events))
            bare_sibling[1]["message"]["content"][0]["input"]["skill"] = "other"
            bare_sibling[3]["message"]["content"][0]["text"] = "Selected the other sibling."
            self.assertEqual(parse(bare_sibling)["sibling_selections"], [f"{plugin}:other"])
            foreign = json.loads(json.dumps(events))
            foreign[1]["message"]["content"][0]["input"]["skill"] = "demo"
            self.assertFalse(parse(foreign)["valid"], "a name outside the staged catalog stays competing")
            both = json.loads(json.dumps(events))
            both.insert(3, json.loads(json.dumps(no_speckit[1])))
            both.insert(4, json.loads(json.dumps(no_speckit[2])))
            self.assertFalse(parse(both)["valid"], "target plus no-op sibling is ambiguous")
            missing = json.loads(json.dumps(events))
            missing[0]["skills"] = [target, f"{plugin}:other"]
            self.assertFalse(parse(missing)["valid"], "inventory must hold every staged sibling")
            stranger = json.loads(json.dumps(events))
            stranger[1]["message"]["content"][0]["input"]["skill"] = "code-review"
            self.assertFalse(parse(stranger)["valid"], "a non-staged skill stays invalid")

            prepared: list[list[str]] = []

            def capture_launch(command: list[str], **kwargs: object) -> FakePopen:
                prepared.append(command.copy())
                return FakePopen(raw)

            with (
                mock.patch.object(claude.shutil, "which", return_value="/usr/local/bin/claude"),
                mock.patch.object(claude.subprocess, "Popen", side_effect=capture_launch),
                mock.patch.object(claude, "cleanup_child"),
            ):
                claude.run_claude_query(
                    "/usr/local/bin/claude", plugin_root, plugin_root / "empty-mcp.json", "query", "sonnet", 30,
                    expected_skill=target, sibling_skills=tuple(sorted(sibling_ids)),
                )
            command = prepared[0]
            allow_index = command.index("--allowedTools") + 1
            self.assertEqual(
                command[allow_index:allow_index + 8],
                [
                    f"Skill({target})", f"Skill({target} *)",
                    f"Skill({plugin}:no-speckit-skill)", f"Skill({plugin}:no-speckit-skill *)",
                    f"Skill({plugin}:other)", f"Skill({plugin}:other *)",
                    f"Skill({plugin}:third)", f"Skill({plugin}:third *)",
                ],
            )
            self.assertEqual(command[command.index("--tools") + 1], "Skill")

    def test_sibling_discovery_walks_only_a_skills_root_and_skips_unreadable_entries(self) -> None:
        engine = import_script(CODEX_ENGINE, "layer2_codex_sibling_roots")
        claude = import_script(CLAUDE_RUNNER, "layer2_claude_sibling_roots")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            loose = root / "SKILL.md"
            loose.write_text("---\nname: demo\ndescription: Demo.\n---\nBody.\n", encoding="utf-8")
            (root / "stranger").mkdir()
            (root / "stranger" / "SKILL.md").write_text("---\nname: stranger\ndescription: S.\n---\n", encoding="utf-8")
            for module in (engine, claude):
                self.assertEqual(module.sibling_skill_dirs(loose), [], "a source outside a skills root has no siblings")
            skills = root / "codex-skills"
            for name in ("demo", "other"):
                (skills / name).mkdir(parents=True)
                (skills / name / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {name}.\n---\n", encoding="utf-8")
            (skills / "notes.md").write_text("not a skill\n", encoding="utf-8")
            locked = skills / "locked"
            locked.mkdir()
            (locked / "SKILL.md").write_text("---\nname: locked\ndescription: L.\n---\n", encoding="utf-8")
            locked.chmod(0)
            try:
                found = engine.sibling_skill_dirs(skills / "demo" / "SKILL.md")
                found_claude = claude.sibling_skill_dirs(skills / "demo" / "SKILL.md")
            finally:
                locked.chmod(0o700)
            readable = sorted([skills / "other"] + ([locked] if os.getuid() == 0 else []))  # root reads a mode-000 dir; discovery returns sorted paths
            self.assertEqual(found, readable, "unreadable siblings are skipped, files are not skills")
            self.assertEqual(found_claude, readable)

    def test_codex_sibling_catalog_requires_every_sibling_exactly_once(self) -> None:
        engine = import_script(CODEX_ENGINE, "layer2_codex_siblings")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skills = root / "codex-skills"
            for name, description in (("demo", "Demo target."), ("other", "Other sibling."), ("third", "Third sibling.")):
                (skills / name).mkdir(parents=True)
                (skills / name / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: {description}\n---\n\nBody of {name}.\n",
                    encoding="utf-8",
                )
            (skills / "notes.md").write_text("not a skill\n", encoding="utf-8")
            workspace = root / "workspace"
            workspace.mkdir()
            marker = engine.selection_marker("demo-eval", "fixed")
            staged = engine.stage_repository_skill(skills / "demo" / "SKILL.md", workspace, "demo-eval", marker)
            siblings, sibling_markers = engine.stage_sibling_skills(
                skills / "demo" / "SKILL.md", workspace, "fixed",
            )
            self.assertEqual(siblings, {
                "other": "Other sibling.",
                "third": "Third sibling.",
                "no-speckit-skill": engine.NO_SPECKIT_SKILL_DESCRIPTION,
            })
            for name in siblings:
                sibling_text = (workspace / ".agents" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertTrue(sibling_text.startswith(f"---\nname: {name}\ndescription: "), "exact frontmatter kept")
                self.assertEqual(sibling_text.count(sibling_markers[name]), 1, "every sibling is attested")
                self.assertNotIn(f"Body of {name}.", sibling_text, "sibling workflow body is not staged")
                self.assertIn("do not run another command", sibling_text, "sibling body stops the trial")
            self.assertFalse((workspace / ".agents" / "skills" / "demo").exists(), "the source target is never staged")
            staged_text = (staged / "SKILL.md").read_text(encoding="utf-8")
            self.assertTrue(
                staged_text.split("\n---\n", 1)[1].lstrip().startswith(engine.MEASUREMENT_STUB_SENTENCE)
            )
            self.assertIn("reply with a chat message whose first line is exactly", staged_text)
            self.assertIn("do not run another command", staged_text)

            witnesses = engine.skill_witnesses(
                workspace, {"demo-eval": marker, **sibling_markers},
            )
            no_speckit_selection = engine.inspect_codex_jsonl(
                codex_stream(witnesses, selected_skill="no-speckit-skill"),
                "demo-eval", witnesses,
            )
            self.assertTrue(no_speckit_selection["valid"])
            self.assertFalse(no_speckit_selection["selected"])
            self.assertEqual(no_speckit_selection["selected_skill"], "no-speckit-skill")

            consultation = engine.inspect_codex_jsonl(
                codex_stream(witnesses, consulted_skill="demo-eval"),
                "demo-eval", witnesses,
            )
            self.assertTrue(consultation["valid"])
            self.assertFalse(consultation["selected"])
            self.assertEqual(consultation["consulted_skills"], ["demo-eval"])
            self.assertEqual(consultation["reason"], "consultation without selection")

            uncorroborated = engine.inspect_codex_jsonl(
                codex_stream(witnesses, message=marker),
                "demo-eval", witnesses,
            )
            self.assertFalse(uncorroborated["valid"])
            self.assertIn("not corroborated", uncorroborated["reason"])

            sibling_selection = engine.inspect_codex_jsonl(
                codex_stream(witnesses, selected_skill="other"),
                "demo-eval", witnesses,
            )
            self.assertTrue(sibling_selection["valid"])
            self.assertFalse(sibling_selection["selected"])
            self.assertEqual(sibling_selection["selected_skill_set"], ["other"])

            ambiguous = engine.inspect_codex_jsonl(
                codex_stream(
                    witnesses,
                    selected_skill="demo-eval",
                    message=f"{marker}\n{sibling_markers['other']}",
                ),
                "demo-eval", witnesses,
            )
            self.assertFalse(ambiguous["valid"])
            self.assertIn("ambiguous", ambiguous["reason"])

            incomplete_events = [
                json.loads(line)
                for line in codex_stream(witnesses, selected_skill="demo-eval").splitlines()
            ]
            del incomplete_events[3]
            incomplete = engine.inspect_codex_jsonl(
                "\n".join(json.dumps(event) for event in incomplete_events),
                "demo-eval", witnesses,
            )
            self.assertFalse(incomplete["valid"])
            self.assertTrue(incomplete["isolation_stop"])

            def catalog(entries: list[str]) -> bytes:
                text = "\n".join(["## Skills", "### Available skills", *entries, "### How to use skills", "- Follow it."])
                return json.dumps([{"text": text}]).encode("utf-8")

            target_entry = f"- demo-eval: Demo target. (file: {(staged / 'SKILL.md').resolve()})"
            sibling_entries = [
                f"- {name}: {description} (file: {(workspace / '.agents' / 'skills' / name / 'SKILL.md').resolve()})"
                for name, description in siblings.items()
            ]
            full = catalog([target_entry, *sibling_entries])
            readiness, reason = engine.inspect_catalog_prompt(
                full, "demo-eval", "Demo target.", staged / "SKILL.md", workspace, siblings
            )
            self.assertIsNotNone(readiness, reason)
            self.assertEqual((readiness["catalog_skill_entries"], readiness["sibling_entries"]), (4, 3))
            self.assertTrue(readiness["sibling_entries_exact"])
            self.assertEqual(sum(entry.startswith("- no-speckit-skill: ") for entry in sibling_entries), 1)
            without_declaration, _ = engine.inspect_catalog_prompt(
                full, "demo-eval", "Demo target.", staged / "SKILL.md", workspace
            )
            self.assertIsNone(without_declaration, "undeclared entries still fail the target-only contract")
            missing_sibling, _ = engine.inspect_catalog_prompt(
                catalog([target_entry, sibling_entries[0]]), "demo-eval", "Demo target.", staged / "SKILL.md", workspace, siblings
            )
            self.assertIsNone(missing_sibling)
            shortened = catalog([target_entry, sibling_entries[0], sibling_entries[1].replace("Third sibling.", "Third.")])
            shortened_readiness, _ = engine.inspect_catalog_prompt(
                shortened, "demo-eval", "Demo target.", staged / "SKILL.md", workspace, siblings
            )
            self.assertIsNone(shortened_readiness, "a shortened sibling description fails")
            extra = catalog([target_entry, *sibling_entries, "- stranger: Stranger. (file: /tmp/stranger/SKILL.md)"])
            extra_readiness, _ = engine.inspect_catalog_prompt(
                extra, "demo-eval", "Demo target.", staged / "SKILL.md", workspace, siblings
            )
            self.assertIsNone(extra_readiness, "an entry outside the staged set fails")
            duplicate = catalog([target_entry, *sibling_entries, sibling_entries[0]])
            duplicate_readiness, _ = engine.inspect_catalog_prompt(
                duplicate, "demo-eval", "Demo target.", staged / "SKILL.md", workspace, siblings
            )
            self.assertIsNone(duplicate_readiness, "a duplicated sibling entry fails")


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Layer2TriggerRunnerTests)
    return run_counted(suite, label="test-trigger-eval-runners")


if __name__ == "__main__":
    raise SystemExit(main())
