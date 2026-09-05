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
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LAYER2 = TESTS_ROOT / "layer2-trigger"
CLAUDE_RUNNER = LAYER2 / "run-trigger-evals.py"
CODEX_RUNNER = LAYER2 / "run-trigger-evals-codex.py"
CODEX_ENGINE = LAYER2 / "run_codex_evals.py"
LOOP_RUNNER = LAYER2 / "run-trigger-loop.py"
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


class Layer2TriggerRunnerTests(unittest.TestCase):
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

            with mock.patch.object(claude.subprocess, "Popen", side_effect=fake_popen):
                rc, launched_stdout, launched_stderr, timed_out = claude.run_claude_query(
                    "/usr/local/bin/claude",
                    plugin_root,
                    mcp_config,
                    "query",
                    "claude-sonnet-test",
                    30,
                )

            timeout_bytes = b'{"type":"system","subtype":"init"}\r\n'
            timeout_stderr = b"partial stderr\r\n"
            timeout_child = FakePopen(timeout_bytes, timeout_stderr)
            timeout_child.timeout = True
            with (
                mock.patch.object(claude.subprocess, "Popen", return_value=timeout_child),
                mock.patch.object(claude.os, "killpg", create=True) as killpg,
            ):
                timeout_rc, timeout_stdout, timeout_error, timeout_state = claude.run_claude_query(
                    "/usr/local/bin/claude",
                    plugin_root,
                    plugin_root / "empty-mcp.json",
                    "query",
                    "claude-sonnet-test",
                    1,
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
            invalid_corpora = ("[]", "{}", "{", '[{"query":"q"}]')
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

            checks = {
                "source description copied exactly": "description: Exact source description." in staged_text,
                "full functional body not copied": "Full body must not copy" not in staged_text,
                "minimal nonce body retained": nonce in staged_text,
                "unique plugin manifest": json.loads(
                    (plugin_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
                )["name"] == plugin_name,
                "exact intended Skill selection": selected["valid"] and selected["selected"],
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
                "direct argv pins strict MCP and model": all(
                    flag in captured["command"]
                    for flag in ("--strict-mcp-config", "--mcp-config", "--model", "--output-format")
                ),
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
                "timeout preserves partial stdout": timeout_state and timeout_rc == -1 and timeout_stdout == timeout_bytes,
                "timeout preserves partial stderr": timeout_error == timeout_stderr,
                "timeout evidence hashes partial bytes": timeout_evidence["stdout_sha256"]
                == hashlib.sha256(timeout_bytes).hexdigest()
                and Path(timeout_evidence["stderr_path"]).read_bytes() == timeout_stderr,
                "timeout terminates owned process group": os.name == "nt" or killpg.call_count == 1,
                "negative one-of-three selection passes": claude.case_passes(False, selected=1, invalid=0),
                "negative two-of-three selection fails": not claude.case_passes(False, selected=2, invalid=0),
                "invalid evidence fails either polarity": not claude.case_passes(False, selected=0, invalid=1)
                and not claude.case_passes(True, selected=3, invalid=1),
                "empty and malformed corpora fail": corpus_results == [None, None, None, None],
                "main executes exactly three trials per selected case": main_exit == 0
                and main_run.call_count == 3
                and len(list(main_evidence.glob("*.jsonl"))) == 3,
                "main report retains threshold and model metadata": main_report["metadata"]["runs_per_query"] == 3
                and main_report["metadata"]["trigger_threshold"] == 0.5
                and main_report["metadata"]["requested_model"] == "claude-sonnet-test",
                "Claude runner never mutates global paths": "shutil.move" not in CLAUDE_RUNNER.read_text(encoding="utf-8")
                and ".claude/" not in CLAUDE_RUNNER.read_text(encoding="utf-8")
                and "auth.json" not in CLAUDE_RUNNER.read_text(encoding="utf-8"),
            }
            for name, condition in checks.items():
                with self.subTest(msg=name):
                    self.assertTrue(condition)

    def test_codex_contracts_remain_unchanged(self) -> None:
        codex = import_script(CODEX_RUNNER, "layer2_codex_wrapper")
        engine = import_script(CODEX_ENGINE, "layer2_codex_engine")
        loop = import_script(LOOP_RUNNER, "layer2_loop_runner")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "SKILL.md"
            source.write_text("---\nname: demo\ndescription: Demo.\n---\n\nBody.\n", encoding="utf-8")
            workspace = root / "workspace"
            workspace.mkdir()
            marker = "CODEX_SKILL_FIRED:demo-eval"
            staged = engine.stage_repository_skill(source, workspace, "demo-eval", marker)
            valid = "\n".join(
                [
                    json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
                    json.dumps({"type": "turn.started"}),
                    json.dumps(
                        {
                            "type": "item.completed",
                            "item": {"type": "agent_message", "text": marker},
                        }
                    ),
                    json.dumps({"type": "turn.completed"}),
                ]
            ).encode("utf-8")
            parsed = engine.inspect_codex_jsonl(valid, marker, requested_model="gpt-5.6-sol")
            competing = engine.inspect_codex_jsonl(
                valid.replace(marker.encode(), b"CODEX_SKILL_FIRED:other"),
                marker,
            )
            failed = engine.inspect_codex_jsonl(
                valid.replace(
                    b'{"type": "turn.completed"}',
                    b'{"type": "error"}\n{"type": "turn.completed"}',
                ),
                marker,
            )
            evidence_dir = root / "evidence"
            evidence_dir.mkdir()
            evidence = engine.retain_run_evidence(evidence_dir, 1, 1, valid, b"stderr\r\n")

            captured: dict[str, object] = {}

            def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
                captured["command"] = command
                captured["kwargs"] = kwargs
                return subprocess.CompletedProcess(command, 0, valid, b"")

            with mock.patch.object(engine.subprocess, "run", side_effect=fake_run):
                rc, stdout, stderr = engine.run_codex_query(
                    workspace,
                    "query",
                    "low",
                    "gpt-5.6-sol",
                    30,
                )

            checks = {
                "imports Codex wrapper": codex is not None,
                "imports trigger loop": loop is not None,
                "all runners avoid shell execution": not any(
                    calls_forbidden_process_api(path)
                    for path in (CLAUDE_RUNNER, CODEX_RUNNER, CODEX_ENGINE, LOOP_RUNNER)
                ),
                "Codex default effort remains low": engine.DEFAULT_REASONING_EFFORT == "low",
                "Codex default model remains approved": engine.DEFAULT_MODEL == "gpt-5.6-sol",
                "Codex skill remains repository scoped": staged == workspace / ".agents" / "skills" / "demo-eval",
                "Codex exact marker remains selected": parsed["valid"] and parsed["selected"],
                "Codex competing marker remains invalid": not competing["valid"],
                "Codex provider error remains invalid": not failed["valid"],
                "Codex requested and unresolved model remain distinct": parsed["requested_model"] == "gpt-5.6-sol"
                and parsed["resolved_model"] is None,
                "Codex raw bytes remain exact": Path(evidence["jsonl_path"]).read_bytes() == valid,
                "Codex raw hash remains exact": evidence["jsonl_sha256"] == hashlib.sha256(valid).hexdigest(),
                "Codex direct result remains binary": (rc, stdout, stderr) == (0, valid, b""),
                "Codex retains existing login environment": captured["kwargs"]["env"].get("PATH")
                == os.environ.get("PATH"),
                "Codex keeps least privilege flags": "--sandbox" in captured["command"]
                and "read-only" in captured["command"]
                and "--ephemeral" in captured["command"],
                "Codex keeps rules enabled": "--ignore-rules" not in captured["command"],
                "Codex negative transport remains fail closed": not engine.case_passes(
                    False, triggers=0, runs=3, threshold=0.5, invalid_runs=1
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
