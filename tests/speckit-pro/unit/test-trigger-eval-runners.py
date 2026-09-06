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
        "skills": [expected_skill],
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
            {"type": "assistant", "message": {"content": [{"type": "text", "text": nonce}]}},
            {"type": "result", "subtype": "success", "is_error": False, "model": "untrusted-result-model"},
        ]
    )
    return ("\r\n".join(json.dumps(event) for event in events) + "\r\n").encode("utf-8")


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


class Layer2TriggerRunnerTests(unittest.TestCase):
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
            self.assertNotIn("FORCE_AUTOUPDATE_PLUGINS", environment)
            expected = {**original, "DISABLE_AUTOUPDATER": "1", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"}
            expected.pop("FORCE_AUTOUPDATE_PLUGINS")
            self.assertTrue(environment == expected, "child environment changed outside the three approved controls")
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
                    inspect.assert_not_called()
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
        plugin = "speckit-pro-eval-fixed"
        target = f"{plugin}:demo-eval-fixed"
        nonce = "CLAUDE_SKILL_SELECTED_fixed"
        raw = claude_stream(root, plugin, target, nonce)
        argument_events = [json.loads(line) for line in raw.splitlines()]
        argument_events[1]["message"]["content"][0]["input"]["args"] = "additional context"
        argument_result = claude.inspect_claude_stream(
            "\n".join(json.dumps(event) for event in argument_events), plugin, root, target, nonce, "sonnet"
        )
        self.assertTrue(argument_result["valid"] and argument_result["selected"])
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
            self.assertEqual(command[allow_index:allow_index + 2], [f"Skill({target})", f"Skill({target} *)"])
            self.assertEqual(command[command.index("--permission-mode") + 1], "dontAsk")
            self.assertEqual(command[command.index("--permission-prompts") + 1], "none")
            self.assertEqual(json.loads(command[command.index("--settings") + 1]), {
                "disableBundledSkills": True, "skillOverrides": {"doctor": "off"},
                "permissions": {"deny": [
                    "Skill(init)", "Skill(init *)", "Skill(security-review)", "Skill(security-review *)"
                ]},
            })
            environment = os.environ.copy()
            environment.update({"DISABLE_AUTOUPDATER": "1", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"})
            environment.pop("FORCE_AUTOUPDATE_PLUGINS", None)
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
            plugin_name = "speckit-pro-eval-fixed"
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
            stream = claude_stream(plugin_root, plugin_name, expected_skill, nonce)
            stream = stream.replace(nonce.encode("utf-8"), f"{nonce} café".encode("utf-8"))
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
                nonselected_stream,
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
                )

            missing_tool_preflights = []
            for omitted_flag in ("--tools", "--allowedTools", "--settings", "--permission-mode", "--permission-prompts"):
                supported_help = " ".join(
                    flag for flag in claude.REQUIRED_FLAGS if flag != omitted_flag
                ).encode("utf-8")
                with (
                    mock.patch.object(claude.shutil, "which", return_value="/usr/local/bin/claude"),
                    mock.patch.object(
                        claude.subprocess,
                        "run",
                        side_effect=[
                            SimpleNamespace(returncode=0, stdout=b"2.1.261\n", stderr=b""),
                            SimpleNamespace(returncode=0, stdout=supported_help, stderr=b""),
                        ],
                    ),
                ):
                    missing_tool_preflights.append(claude.cli_preflight("/usr/local/bin/claude"))

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
            main_plugin_name = f"speckit-pro-eval-{fixed_id}"
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
                    return_value=(0, main_stream, b"", False),
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
                "nonce alone does not select": nonce_only["valid"] and not nonce_only["selected"],
                "nonce absence does not suppress selection": no_nonce["valid"] and no_nonce["selected"],
                "every malformed or competing selection fails": all(
                    not result["valid"] for result in mutation_results.values()
                ),
                "invalid UTF-8 fails semantic parsing": not invalid_utf8_result["valid"],
                "raw CRLF stdout retained byte-for-byte": Path(raw_evidence["stdout_path"]).read_bytes() == stream,
                "raw non-UTF8 stderr retained byte-for-byte": Path(raw_evidence["stderr_path"]).read_bytes()
                == b"stderr\r\n\xff",
                "raw hashes cover actual bytes": raw_evidence["stdout_sha256"] == hashlib.sha256(stream).hexdigest(),
                "direct argv uses restricted session plugin": captured["command"][:3]
                == ["/usr/local/bin/claude", "--restricted", "--plugin-dir"],
                "direct argv and preflight pin Skill-only tools": all(
                    flag in captured["command"]
                    for flag in ("--strict-mcp-config", "--mcp-config", "--model", "--output-format")
                )
                and captured["command"].count("--tools") == 1
                and captured["command"][captured["command"].index("--tools") + 1] == "Skill"
                and captured["command"].count("--allowedTools") == 1
                and captured["command"][captured["command"].index("--allowedTools") + 1] == f"Skill({expected_skill})"
                and all(result is None for result, _reason in missing_tool_preflights),
                "direct argv uses no persistence": "--no-session-persistence" in captured["command"],
                "direct launch inherits environment": captured["kwargs"]["env"].get("PATH") == os.environ.get("PATH"),
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
                    and evidence_files == []
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
                    plugin_name = f"speckit-pro-eval-{fixed_id}"
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
                            side_effect=trial_results,
                        ),
                        contextlib.redirect_stdout(output),
                    ):
                        exit_code = claude.main(["demo", "--model", "claude-sonnet-test"])
                    report = json.loads(output.getvalue())
                    self.assertEqual(exit_code, 0)
                    self.assertEqual(report["summary"]["resolved_model"], expected)

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
            self.assertEqual(probe.call_args.kwargs["executable"], shutil.which("codex"))
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

        marker = "CODEX_SKILL_FIRED:demo-eval"
        base = [
            {"type": "thread.started", "thread_id": "thread-1"},
            {"type": "turn.started"},
            {"type": "item.completed", "item": {"type": "agent_message", "text": marker}},
            {"type": "turn.completed"},
        ]
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
                parsed = engine.inspect_codex_jsonl("\n".join(map(json.dumps, [*base[:2], event, *base[2:]])), marker)
                self.assertFalse(parsed["valid"])
                self.assertTrue(parsed["isolation_stop"])
        unavailable = {"type": "item.completed", "item": {"type": "error", "message": "tool unavailable"}}
        denied = engine.inspect_codex_jsonl("\n".join(map(json.dumps, [*base[:2], unavailable, *base[2:]])), marker)
        self.assertFalse(denied["valid"])
        self.assertFalse(denied.get("isolation_stop", False))
        local = {"type": "item.completed", "item": {"type": "command_execution", "status": "completed", "exit_code": 0}}
        self.assertTrue(engine.inspect_codex_jsonl("\n".join(map(json.dumps, [*base[:2], local, *base[2:]])), marker)["valid"])
        for malformed in ({"type": []}, {"type": "item.started", "item": {"type": []}}):
            with self.subTest(malformed=malformed):
                parsed = engine.inspect_codex_jsonl(json.dumps(malformed), marker)
                self.assertFalse(parsed["valid"])
                self.assertTrue(parsed["isolation_stop"])

    def test_codex_isolation_violation_retains_evidence_and_stops(self) -> None:
        engine = import_script(CODEX_ENGINE, "layer2_codex_isolation_stop")
        for item_type, expected_calls in (("mcp_tool_call", 1), ("error", 2)):
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
            marker = "CODEX_SKILL_FIRED:demo-eval"
            with mock.patch.object(engine.shutil, "copy2") as credential_copy:
                staged = engine.stage_repository_skill(source, workspace, "demo-eval", marker)
            valid = "\n".join(
                [
                    json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
                    json.dumps({"type": "turn.started"}),
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
            parsed = engine.inspect_codex_jsonl(valid, marker, requested_model="gpt-5.6-sol")
            competing = engine.inspect_codex_jsonl(
                valid.replace(b"Done.", b"CODEX_SKILL_FIRED:other"),
                marker,
            )
            marker_not_first = engine.inspect_codex_jsonl(
                valid.replace(
                    f"{marker}\\nDone.".encode(),
                    f"Progress\\n{marker}".encode(),
                ),
                marker,
            )
            missing_lifecycle = engine.inspect_codex_jsonl(
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"type": "agent_message", "text": marker},
                    }
                ),
                marker,
            )
            wrong_order = engine.inspect_codex_jsonl(
                "\n".join(
                    [
                        json.dumps({"type": "turn.completed"}),
                        json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
                        json.dumps({"type": "turn.started"}),
                    ]
                ),
                marker,
            )
            no_response = engine.inspect_codex_jsonl(
                "\n".join(
                    [
                        json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
                        json.dumps({"type": "turn.started"}),
                        json.dumps({"type": "turn.completed"}),
                    ]
                ),
                marker,
            )
            top_error = engine.inspect_codex_jsonl(
                valid.replace(
                    b'{"type": "turn.completed"}',
                    b'{"type": "error"}\n{"type": "turn.completed"}',
                ),
                marker,
            )
            item_error = engine.inspect_codex_jsonl(
                valid.replace(
                    b'{"type": "item.completed", "item": {"type": "agent_message", "text": "Preparing to answer."}}',
                    b'{"type": "item.completed", "item": {"type": "error", "message": "failed"}}',
                ),
                marker,
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
                    marker,
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
                marker,
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
            invalid_utf8_result = engine.inspect_codex_jsonl(invalid_utf8, marker)

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

            def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
                captured["command"] = command
                captured["kwargs"] = kwargs
                return subprocess.CompletedProcess(command, 0, valid, b"")

            with (
                mock.patch.dict(os.environ, {"CODEX_HOME": str(auth_home)}, clear=False),
                mock.patch.object(engine.subprocess, "run", side_effect=fake_run),
            ):
                rc, stdout, stderr, timed_out = engine.run_codex_query(
                    workspace,
                    "query",
                    "low",
                    "gpt-5.6-sol",
                    30,
                    isolation_args,
                )

            timeout_stdout = b"partial-jsonl\r\n"
            timeout_stderr = b"partial-stderr\r\n"
            timeout_evidence_dir = root / "timeout-evidence"
            timeout_evidence_dir.mkdir()
            with mock.patch.object(
                engine.subprocess,
                "run",
                side_effect=subprocess.TimeoutExpired(
                    ["codex"],
                    7,
                    output=timeout_stdout,
                    stderr=timeout_stderr,
                ),
            ):
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
                "run",
                return_value=subprocess.CompletedProcess(
                    [],
                    -1,
                    b"signal-output",
                    b"signal-stderr",
                ),
            ):
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
                and preflight_captured["kwargs"]["executable"] == shutil.which("codex")
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
                == shutil.which("codex"),
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
                and 'model_reasoning_effort="low"' in captured["command"],
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
                    and evidence_files == []
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


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Layer2TriggerRunnerTests)
    return run_counted(suite, label="test-trigger-eval-runners")


if __name__ == "__main__":
    raise SystemExit(main())
