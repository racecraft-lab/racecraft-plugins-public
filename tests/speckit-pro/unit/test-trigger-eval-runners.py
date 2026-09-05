#!/usr/bin/env python3
"""Deterministic Layer-4 contracts for the Python Layer-2 trigger runners."""

from __future__ import annotations

import ast
from contextlib import redirect_stderr
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import textwrap
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


CURRENT_INVENTORY = [
    "imports the Claude trigger runner",
    "imports the Codex trigger runner",
    "imports the trigger-loop runner",
    "Claude wrapper creates a POSIX launcher",
    "Claude wrapper creates a Windows launcher",
    "Claude wrapper creates a Python launcher",
    "Python launcher prepends --settings",
    "Python launcher preserves incoming arguments",
    "Python launcher appends --bare",
    "Python launcher propagates the Claude exit code",
    "settings-only branch reports wrapper plus --settings",
    "direct branch reports no wrapper path",
    "move_aside delegates cross-filesystem moves to shutil.move",
    "move_aside rejects an existing target without moving the source",
    "restore_moves reports a restoration collision",
    "restore_moves leaves the backup intact after a collision",
    "restore_moves restores a backup when the original is absent",
    "Codex --run checks for the codex executable",
    "Codex --run delegates through the current Python executable",
    "Codex --run strips every --run control flag",
    "Codex --run preserves all remaining arguments",
    "trigger loop delegates through the current Python executable",
    "trigger loop preserves the exact run_loop command and flags",
    "Layer-2 command argv contains no hard-coded python3 token",
    "Layer-2 runners never enable shell=True",
    "Layer-2 runners never call os.system",
    "Codex trigger engine defaults to supported low reasoning",
    "Codex trigger engine defaults to the approved model",
    "Codex stages the exact marked skill under repository .agents",
    "Codex staging never copies a credential file",
    "Codex invocation keeps the existing login environment",
    "Codex invocation uses explicit model effort JSON and least privilege",
    "Codex invocation retains applicable execution rules",
    "Codex selection requires a successful JSON lifecycle",
    "Codex selection ignores started copies and allows prior completed progress",
    "Codex selection requires the exact staged marker first in its completed message",
    "Codex selection rejects a competing marker",
    "Codex selection rejects an out-of-order lifecycle",
    "Codex selection rejects nested provider errors",
    "Codex selection distinguishes requested from unresolved model",
    "Codex raw JSONL and stderr retain exact bytes and hashes",
    "Codex cleanup reports disposable repository residue",
    "Codex rejects unreadable, malformed, non-list, and invalid cases before subprocess",
    "Codex failed transport cannot pass a negative case",
    "Claude invocation propagates an explicit model",
    "Claude result validation rejects failed cases despite exit zero",
    "Claude result validation rejects incomplete trial denominators",
    "Claude result validation rejects duplicate or missing query roster",
    "Claude result validation rejects wrong expected polarity",
    "Claude result validation rejects inconsistent trigger accounting",
    "Claude rejects malformed corpus before any subprocess",
    "Claude retains exact output hashes and distinguishes unresolved model",
]


class ExecIntercept(RuntimeError):
    """Stop an exec-family mock after recording its arguments."""


def import_script(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import script: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_local_claude_stub(root: Path, record_path: Path, exit_code: int) -> Path:
    """Create a local executable named like the platform's Claude command."""
    stub_source = textwrap.dedent(
        f"""\
        import json
        from pathlib import Path
        import sys

        Path({str(record_path)!r}).write_text(json.dumps(sys.argv[1:]), encoding="utf-8")
        raise SystemExit({exit_code})
        """
    )
    if os.name == "nt":
        script = root / "claude-stub.py"
        script.write_text(stub_source, encoding="utf-8")
        launcher = root / "claude.cmd"
        launcher.write_text(
            f'@"{sys.executable}" "{script}" %*\r\n@exit /b %ERRORLEVEL%\r\n',
            encoding="utf-8",
        )
        return launcher

    launcher = root / "claude"
    launcher.write_text(f"#!{sys.executable}\n{stub_source}", encoding="utf-8")
    launcher.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    return launcher


def python3_in_command_argv(path: Path) -> bool:
    """Find hard-coded ``python3`` tokens in command/exec argument vectors."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple)):
            if any(isinstance(item, ast.Constant) and item.value == "python3" for item in node.elts):
                return True
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr.startswith("exec"):
            for argument in node.args[:2]:
                if isinstance(argument, ast.Constant) and argument.value == "python3":
                    return True
    return False


def has_shell_true(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return any(
        isinstance(node, ast.Call)
        and any(
            keyword.arg == "shell"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
            for keyword in node.keywords
        )
        for node in ast.walk(tree)
    )


def calls_os_system(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "os"
        and node.func.attr == "system"
        for node in ast.walk(tree)
    )


class Layer2TriggerRunnerTests(unittest.TestCase):
    def test_layer2_trigger_runner_contracts(self) -> None:
        claude = import_script(CLAUDE_RUNNER, "xplat010_layer2_claude_runner")
        codex = import_script(CODEX_RUNNER, "xplat010_layer2_codex_runner")
        codex_engine = import_script(CODEX_ENGINE, "xplat010_layer2_codex_engine")
        loop = import_script(LOOP_RUNNER, "xplat010_layer2_loop_runner")
        source_paths = (CLAUDE_RUNNER, CODEX_RUNNER, CODEX_ENGINE, LOOP_RUNNER)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            wrapper_dir = root / "wrappers"
            wrapper_dir.mkdir()
            stub_dir = root / "stub-bin"
            stub_dir.mkdir()
            settings_file = root / "settings.json"
            settings_file.write_text("{}\n", encoding="utf-8")
            stub_record = root / "claude-argv.json"
            write_local_claude_stub(stub_dir, stub_record, exit_code=37)
            wrapper_env = os.environ.copy()
            wrapper_env["PATH"] = f"{stub_dir}{os.pathsep}{wrapper_env.get('PATH', '')}"
            if os.name == "nt":
                wrapper_env["PATHEXT"] = ".COM;.EXE;.BAT;.CMD"

            claude.write_claude_wrapper(wrapper_dir, settings_file, True, wrapper_env)
            posix_launcher = wrapper_dir / "claude"
            windows_launcher = wrapper_dir / "claude.cmd"
            python_launchers = sorted(wrapper_dir.glob("*.py"))
            python_launcher = python_launchers[0] if len(python_launchers) == 1 else None
            if python_launcher is None:
                wrapper_result = subprocess.CompletedProcess([], 127, "", "Python launcher not found")
            else:
                wrapper_result = subprocess.run(
                    [sys.executable, str(python_launcher), "alpha", "two words"],
                    text=True,
                    capture_output=True,
                    env=wrapper_env,
                    shell=False,
                    check=False,
                )
            wrapper_argv = (
                json.loads(stub_record.read_text(encoding="utf-8")) if stub_record.is_file() else []
            )

            claude_fixture_root = root / "claude-fixture"
            claude_plugin_root = claude_fixture_root / "speckit-pro"
            (claude_plugin_root / "skills" / "demo").mkdir(parents=True)
            claude_eval = (
                claude_fixture_root
                / "tests"
                / "speckit-pro"
                / "layer2-trigger"
                / "evals"
                / "demo-trigger.json"
            )
            claude_eval.parent.mkdir(parents=True)
            claude_eval.write_text("[]\n", encoding="utf-8")
            claude.PLUGIN_ROOT = claude_plugin_root
            fake_home = root / "fake-home"
            fake_home.mkdir()
            skill_creator = root / "claude-skill-creator"
            skill_creator.mkdir()

            settings_only_stderr = io.StringIO()
            settings_only_evidence = root / "settings-only-evidence"
            with (
                mock.patch.dict(
                    os.environ,
                    {
                        "HOME": str(fake_home),
                        "PATH": wrapper_env.get("PATH", ""),
                        "SKILL_CREATOR_ROOT": str(skill_creator),
                        "EVAL_DISABLE_PLUGINS": "other-plugin@test",
                    },
                    clear=True,
                ),
                mock.patch.object(
                    claude.subprocess,
                    "run",
                    return_value=SimpleNamespace(
                        returncode=0,
                        stdout=json.dumps(
                            {
                                "results": [],
                                "summary": {"total": 0, "passed": 0, "failed": 0},
                            }
                        ),
                        stderr="",
                    ),
                ) as settings_only_run,
                mock.patch.object(claude, "write_claude_wrapper", wraps=claude.write_claude_wrapper) as settings_wrap,
                redirect_stderr(settings_only_stderr),
            ):
                settings_only_exit = claude.main(["demo", "--evidence-dir", str(settings_only_evidence)])

            direct_mode_stderr = io.StringIO()
            direct_mode_evidence = root / "direct-mode-evidence"
            with (
                mock.patch.dict(
                    os.environ,
                    {
                        "HOME": str(fake_home),
                        "PATH": wrapper_env.get("PATH", ""),
                        "SKILL_CREATOR_ROOT": str(skill_creator),
                    },
                    clear=True,
                ),
                mock.patch.object(
                    claude.subprocess,
                    "run",
                    return_value=SimpleNamespace(
                        returncode=0,
                        stdout=json.dumps(
                            {
                                "results": [],
                                "summary": {"total": 0, "passed": 0, "failed": 0},
                            }
                        ),
                        stderr="",
                    ),
                ) as direct_mode_run,
                mock.patch.object(claude, "write_claude_wrapper", wraps=claude.write_claude_wrapper) as direct_wrap,
                redirect_stderr(direct_mode_stderr),
            ):
                direct_mode_exit = claude.main(
                    [
                        "demo",
                        "--model",
                        "claude-sonnet-test",
                        "--evidence-dir",
                        str(direct_mode_evidence),
                    ]
                )

            failed_summary = json.dumps(
                {
                    "results": [
                        {
                            "query": "q",
                            "should_trigger": True,
                            "trigger_rate": 0.0,
                            "triggers": 0,
                            "runs": 3,
                            "pass": False,
                        }
                    ],
                    "summary": {"total": 1, "passed": 0, "failed": 1},
                }
            )
            incomplete_trials = json.dumps(
                {
                    "results": [
                        {
                            "query": "q",
                            "should_trigger": True,
                            "trigger_rate": 1.0,
                            "triggers": 1,
                            "runs": 1,
                            "pass": True,
                        }
                    ],
                    "summary": {"total": 1, "passed": 1, "failed": 0},
                }
            )
            failed_summary_valid, _failed_summary_reason = claude.validate_eval_result(
                failed_summary,
                expected_cases=[{"query": "q", "should_trigger": True}],
                runs_per_query=3,
                trigger_threshold=0.5,
            )
            incomplete_trials_valid, _incomplete_trials_reason = claude.validate_eval_result(
                incomplete_trials,
                expected_cases=[{"query": "q", "should_trigger": True}],
                runs_per_query=3,
                trigger_threshold=0.5,
            )
            duplicate_result = json.dumps(
                {
                    "results": [
                        {
                            "query": "first",
                            "should_trigger": True,
                            "trigger_rate": 1.0,
                            "triggers": 3,
                            "runs": 3,
                            "pass": True,
                        },
                        {
                            "query": "first",
                            "should_trigger": True,
                            "trigger_rate": 1.0,
                            "triggers": 3,
                            "runs": 3,
                            "pass": True,
                        },
                    ],
                    "summary": {"total": 2, "passed": 2, "failed": 0},
                }
            )
            duplicate_result_valid, _duplicate_reason = claude.validate_eval_result(
                duplicate_result,
                expected_cases=[
                    {"query": "first", "should_trigger": True},
                    {"query": "second", "should_trigger": False},
                ],
                runs_per_query=3,
                trigger_threshold=0.5,
            )
            wrong_polarity = json.dumps(
                {
                    "results": [
                        {
                            "query": "q",
                            "should_trigger": False,
                            "trigger_rate": 0.0,
                            "triggers": 0,
                            "runs": 3,
                            "pass": True,
                        }
                    ],
                    "summary": {"total": 1, "passed": 1, "failed": 0},
                }
            )
            wrong_polarity_valid, _wrong_polarity_reason = claude.validate_eval_result(
                wrong_polarity,
                expected_cases=[{"query": "q", "should_trigger": True}],
                runs_per_query=3,
                trigger_threshold=0.5,
            )
            inconsistent_rate = json.dumps(
                {
                    "results": [
                        {
                            "query": "q",
                            "should_trigger": True,
                            "trigger_rate": 1.0,
                            "triggers": 2,
                            "runs": 3,
                            "pass": True,
                        }
                    ],
                    "summary": {"total": 1, "passed": 1, "failed": 0},
                }
            )
            inconsistent_rate_valid, _inconsistent_rate_reason = claude.validate_eval_result(
                inconsistent_rate,
                expected_cases=[{"query": "q", "should_trigger": True}],
                runs_per_query=3,
                trigger_threshold=0.5,
            )
            claude_eval.write_text(
                json.dumps([{"query": "q", "should_trigger": True}]) + "\n",
                encoding="utf-8",
            )
            with (
                mock.patch.dict(
                    os.environ,
                    {
                        "HOME": str(fake_home),
                        "PATH": wrapper_env.get("PATH", ""),
                        "SKILL_CREATOR_ROOT": str(skill_creator),
                    },
                    clear=True,
                ),
                mock.patch.object(
                    claude.subprocess,
                    "run",
                    return_value=SimpleNamespace(
                        returncode=0,
                        stdout=failed_summary,
                        stderr="",
                    ),
                ),
            ):
                failed_mode_exit = claude.main(
                    [
                        "demo",
                        "--model",
                        "claude-sonnet-test",
                        "--evidence-dir",
                        str(root / "failed-mode-evidence"),
                    ]
                )

            claude_eval.write_text("{", encoding="utf-8")
            with (
                mock.patch.dict(
                    os.environ,
                    {
                        "HOME": str(fake_home),
                        "PATH": wrapper_env.get("PATH", ""),
                        "SKILL_CREATOR_ROOT": str(skill_creator),
                    },
                    clear=True,
                ),
                mock.patch.object(claude.subprocess, "run") as malformed_claude_run,
            ):
                malformed_claude_exit = claude.main(["demo"])
            claude_eval.write_text(
                json.dumps([{"query": "q", "should_trigger": True}]) + "\n",
                encoding="utf-8",
            )

            direct_evidence_record = json.loads(
                (direct_mode_evidence / "evidence.json").read_text(encoding="utf-8")
            )

            move_source = root / "move-source"
            move_source.write_text("source", encoding="utf-8")
            move_target = root / "move-target"
            with mock.patch.object(claude.shutil, "move", return_value=str(move_target)) as move_mock:
                move_result = claude.move_aside(move_source, move_target, "moved", "move failed")
            move_call = move_mock.call_args

            collision_source = root / "collision-source"
            collision_source.write_text("source", encoding="utf-8")
            collision_target = root / "collision-target"
            collision_target.write_text("target", encoding="utf-8")
            with mock.patch.object(claude.shutil, "move") as collision_move:
                collision_result = claude.move_aside(
                    collision_source,
                    collision_target,
                    "moved",
                    "move failed",
                )

            restore_original = root / "restore-original"
            restore_original.write_text("collision", encoding="utf-8")
            restore_backup = root / "restore-backup"
            restore_backup.write_text("backup", encoding="utf-8")
            restore_stderr = io.StringIO()
            with redirect_stderr(restore_stderr):
                claude.restore_moves([(restore_original, restore_backup)])

            success_original = root / "success-original"
            success_backup = root / "success-backup"
            success_backup.write_text("restored", encoding="utf-8")
            claude.restore_moves([(success_original, success_backup)])

            fixture_root = root / "fixture-root"
            plugin_root = fixture_root / "speckit-pro"
            (plugin_root / "codex-skills" / "demo").mkdir(parents=True)
            codex_eval = (
                fixture_root
                / "tests"
                / "speckit-pro"
                / "layer2-trigger"
                / "codex-evals"
                / "demo-trigger.json"
            )
            codex_eval.parent.mkdir(parents=True)
            codex_eval.write_text("{}\n", encoding="utf-8")
            codex.PLUGIN_ROOT = plugin_root

            codex_skill_source = plugin_root / "codex-skills" / "demo" / "SKILL.md"
            codex_skill_source.write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n\nDo the demo.\n",
                encoding="utf-8",
            )
            staged_workspace = root / "codex-workspace"
            staged_workspace.mkdir()
            auth_home = root / "existing-codex-home"
            auth_home.mkdir()
            auth_file = auth_home / "auth.json"
            auth_file.write_text("credential sentinel\n", encoding="utf-8")
            exact_skill_name = "demo-eval-exact"
            exact_marker = f"CODEX_SKILL_FIRED:{exact_skill_name}"
            with mock.patch.object(codex_engine.shutil, "copy2") as copy_mock:
                staged_skill_dir = codex_engine.stage_repository_skill(
                    codex_skill_source,
                    staged_workspace,
                    exact_skill_name,
                    exact_marker,
                )

            valid_jsonl = "\n".join(
                [
                    json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
                    json.dumps({"type": "turn.started"}),
                    json.dumps(
                        {
                            "type": "item.started",
                            "item": {
                                "id": "item-start-copy",
                                "type": "agent_message",
                                "text": exact_marker,
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "type": "item.updated",
                            "item": {
                                "id": "item-start-copy",
                                "type": "agent_message",
                                "text": exact_marker,
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "type": "item.completed",
                            "item": {
                                "id": "item-progress",
                                "type": "agent_message",
                                "text": "Preparing to answer.",
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "type": "item.completed",
                            "item": {
                                "id": "item-1",
                                "type": "agent_message",
                                "text": f"{exact_marker}\nProceeding with the exact staged skill.",
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "type": "turn.completed",
                            "usage": {"input_tokens": 1, "output_tokens": 1},
                        }
                    ),
                ]
            )
            competing_jsonl = valid_jsonl.replace(
                "Proceeding with the exact staged skill.",
                "CODEX_SKILL_FIRED:other-eval-skill",
            )
            valid_evidence = codex_engine.inspect_codex_jsonl(valid_jsonl, exact_marker)
            missing_lifecycle_evidence = codex_engine.inspect_codex_jsonl(
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"type": "agent_message", "text": exact_marker},
                    }
                ),
                exact_marker,
            )
            competing_evidence = codex_engine.inspect_codex_jsonl(competing_jsonl, exact_marker)
            wrong_order_jsonl = "\n".join(
                [
                    json.dumps({"type": "turn.completed"}),
                    json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
                    json.dumps({"type": "turn.started"}),
                ]
            )
            wrong_order_evidence = codex_engine.inspect_codex_jsonl(wrong_order_jsonl, exact_marker)
            nested_error_jsonl = valid_jsonl.replace(
                '"text": "Preparing to answer."',
                '"text": "Preparing to answer.", "error": {"message": "provider failed"}',
            )
            nested_error_evidence = codex_engine.inspect_codex_jsonl(nested_error_jsonl, exact_marker)
            model_evidence = codex_engine.inspect_codex_jsonl(
                valid_jsonl,
                exact_marker,
                requested_model="gpt-5.6-sol",
            )
            raw_evidence_dir = root / "codex-raw-evidence"
            raw_evidence_dir.mkdir()
            raw_evidence = codex_engine.retain_run_evidence(
                raw_evidence_dir,
                1,
                1,
                valid_jsonl,
                "provider stderr\n",
            )
            residue_workspace = root / "residue-workspace"
            residue_workspace.mkdir()
            with mock.patch.object(codex_engine.shutil, "rmtree", return_value=None):
                cleanup_residue = codex_engine.remove_workspace(residue_workspace)

            unreadable_codex_corpus = root / "unreadable-codex-corpus"
            unreadable_codex_corpus.mkdir()
            invalid_codex_corpora = []
            for name, body in (
                ("malformed", "{"),
                ("non-list", "{}\n"),
                ("invalid-case", '[{"query": "q"}]\n'),
            ):
                path = root / f"{name}-codex-corpus.json"
                path.write_text(body, encoding="utf-8")
                invalid_codex_corpora.append(path)
            invalid_codex_corpora.append(unreadable_codex_corpus)
            invalid_codex_subprocess_calls = 0
            invalid_codex_messages = []
            for invalid_codex_corpus in invalid_codex_corpora:
                with (
                    mock.patch.object(codex_engine, "find_eval_file", return_value=invalid_codex_corpus),
                    mock.patch.object(codex_engine, "find_skill_source", return_value=codex_skill_source),
                    mock.patch.object(codex_engine.subprocess, "run") as invalid_codex_run,
                    mock.patch.object(sys, "argv", [str(CODEX_ENGINE), "demo"]),
                    self.assertRaises(SystemExit) as invalid_codex_exit,
                ):
                    codex_engine.main()
                invalid_codex_subprocess_calls += invalid_codex_run.call_count
                invalid_codex_messages.append(str(invalid_codex_exit.exception))

            with (
                mock.patch.dict(os.environ, {"CODEX_HOME": str(auth_home)}, clear=False),
                mock.patch.object(
                    codex_engine.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess([], 0, valid_jsonl, ""),
                ) as codex_run,
            ):
                codex_rc, codex_stdout, codex_stderr = codex_engine.run_codex_query(
                    staged_workspace,
                    "query without the private marker",
                    "low",
                    "gpt-5.6-sol",
                    30,
                )
            codex_command = list(codex_run.call_args.args[0])
            codex_env = codex_run.call_args.kwargs["env"]

            exec_mocks: dict[str, mock.Mock] = {}
            with mock.patch.object(codex.shutil, "which", return_value=str(root / "codex")) as which_mock:
                with mock.patch.object(codex.os, "execv", side_effect=ExecIntercept) as execv_mock:
                    with mock.patch.object(codex.os, "execve", side_effect=ExecIntercept) as execve_mock:
                        with mock.patch.object(codex.os, "execvp", side_effect=ExecIntercept) as execvp_mock:
                            exec_mocks = {
                                "execv": execv_mock,
                                "execve": execve_mock,
                                "execvp": execvp_mock,
                            }
                            with self.assertRaises(ExecIntercept):
                                codex.main(["demo", "--run", "--profile", "fast", "--run", "tail"])
            exec_calls = [
                (name, call_mock.call_args.args)
                for name, call_mock in exec_mocks.items()
                if call_mock.call_args is not None
            ]
            exec_args = exec_calls[0][1] if len(exec_calls) == 1 else ()
            delegated_executable = exec_args[0] if len(exec_args) >= 1 else None
            delegated_argv = list(exec_args[1]) if len(exec_args) >= 2 else []

            skill_creator = root / "skill-creator"
            skill_creator.mkdir()
            (plugin_root / "skills" / "demo").mkdir(parents=True)
            loop_eval = (
                fixture_root
                / "tests"
                / "speckit-pro"
                / "layer2-trigger"
                / "evals"
                / "demo-trigger.json"
            )
            loop_eval.parent.mkdir(parents=True, exist_ok=True)
            loop_eval.write_text("{}\n", encoding="utf-8")
            loop.PLUGIN_ROOT = plugin_root
            with mock.patch.dict(os.environ, {"SKILL_CREATOR_ROOT": str(skill_creator)}, clear=False):
                with mock.patch.object(
                    loop.subprocess,
                    "run",
                    return_value=SimpleNamespace(returncode=0),
                ) as run_mock:
                    loop_returncode = loop.main(["demo"])
            loop_call = run_mock.call_args
            loop_command = list(loop_call.args[0]) if loop_call is not None else []
            expected_loop_command = [
                sys.executable,
                "-m",
                "scripts.run_loop",
                "--eval-set",
                str(plugin_root / "../tests/speckit-pro/layer2-trigger/evals/demo-trigger.json"),
                "--skill-path",
                str(plugin_root / "skills" / "demo"),
                "--max-iterations",
                "5",
                "--holdout",
                "0.4",
                "--runs-per-query",
                "3",
                "--trigger-threshold",
                "0.5",
                "--verbose",
            ]

            checks = [
                (CURRENT_INVENTORY[0], lambda: self.assertIsNotNone(claude)),
                (CURRENT_INVENTORY[1], lambda: self.assertIsNotNone(codex)),
                (CURRENT_INVENTORY[2], lambda: self.assertIsNotNone(loop)),
                (CURRENT_INVENTORY[3], lambda: self.assertTrue(posix_launcher.is_file())),
                (CURRENT_INVENTORY[4], lambda: self.assertTrue(windows_launcher.is_file())),
                (CURRENT_INVENTORY[5], lambda: self.assertEqual(len(python_launchers), 1)),
                (
                    CURRENT_INVENTORY[6],
                    lambda: self.assertEqual(wrapper_argv[:2], ["--settings", str(settings_file)]),
                ),
                (CURRENT_INVENTORY[7], lambda: self.assertEqual(wrapper_argv[2:4], ["alpha", "two words"])),
                (CURRENT_INVENTORY[8], lambda: self.assertEqual(wrapper_argv[-1:], ["--bare"])),
                (CURRENT_INVENTORY[9], lambda: self.assertEqual(wrapper_result.returncode, 37)),
                (
                    CURRENT_INVENTORY[10],
                    lambda: self.assertTrue(
                        settings_only_exit == 0
                        and settings_wrap.call_count == 1
                        and "Using Claude wrapper with --settings only for 'demo'" in settings_only_stderr.getvalue()
                        and settings_only_run.call_args is not None
                    ),
                ),
                (
                    CURRENT_INVENTORY[11],
                    lambda: self.assertTrue(
                        direct_mode_exit == 0
                        and direct_wrap.call_count == 0
                        and "Running Claude directly (no wrapper, no --settings, no --bare) for 'demo'"
                        in direct_mode_stderr.getvalue()
                        and direct_mode_run.call_args is not None
                    ),
                ),
                (
                    CURRENT_INVENTORY[12],
                    lambda: self.assertTrue(
                        move_result
                        and move_call is not None
                        and tuple(Path(argument) for argument in move_call.args)
                        == (move_source, move_target)
                    ),
                ),
                (
                    CURRENT_INVENTORY[13],
                    lambda: self.assertTrue(
                        not collision_result
                        and collision_source.is_file()
                        and collision_source.read_text(encoding="utf-8") == "source"
                        and collision_move.call_count == 0
                    ),
                ),
                (
                    CURRENT_INVENTORY[14],
                    lambda: self.assertTrue(
                        "cannot restore" in restore_stderr.getvalue().lower()
                        and str(restore_original) in restore_stderr.getvalue()
                        and str(restore_backup) in restore_stderr.getvalue()
                    ),
                ),
                (
                    CURRENT_INVENTORY[15],
                    lambda: self.assertTrue(
                        restore_backup.is_file()
                        and restore_backup.read_text(encoding="utf-8") == "backup"
                    ),
                ),
                (
                    CURRENT_INVENTORY[16],
                    lambda: self.assertTrue(
                        success_original.is_file()
                        and success_original.read_text(encoding="utf-8") == "restored"
                        and not success_backup.exists()
                    ),
                ),
                (
                    CURRENT_INVENTORY[17],
                    lambda: self.assertEqual(which_mock.call_args_list, [mock.call("codex")]),
                ),
                (
                    CURRENT_INVENTORY[18],
                    lambda: self.assertTrue(
                        len(exec_calls) == 1
                        and delegated_executable == sys.executable
                        and delegated_argv[:1] == [sys.executable]
                    ),
                ),
                (CURRENT_INVENTORY[19], lambda: self.assertNotIn("--run", delegated_argv)),
                (
                    CURRENT_INVENTORY[20],
                    lambda: self.assertEqual(delegated_argv[2:], ["demo", "--profile", "fast", "tail"]),
                ),
                (
                    CURRENT_INVENTORY[21],
                    lambda: self.assertTrue(loop_returncode == 0 and loop_command[:1] == [sys.executable]),
                ),
                (CURRENT_INVENTORY[22], lambda: self.assertEqual(loop_command, expected_loop_command)),
                (
                    CURRENT_INVENTORY[23],
                    lambda: self.assertFalse(any(python3_in_command_argv(path) for path in source_paths)),
                ),
                (
                    CURRENT_INVENTORY[24],
                    lambda: self.assertFalse(any(has_shell_true(path) for path in source_paths)),
                ),
                (
                    CURRENT_INVENTORY[25],
                    lambda: self.assertFalse(any(calls_os_system(path) for path in source_paths)),
                ),
                (
                    CURRENT_INVENTORY[26],
                    lambda: self.assertEqual(codex_engine.DEFAULT_REASONING_EFFORT, "low"),
                ),
                (
                    CURRENT_INVENTORY[27],
                    lambda: self.assertEqual(codex_engine.DEFAULT_MODEL, "gpt-5.6-sol"),
                ),
                (
                    CURRENT_INVENTORY[28],
                    lambda: self.assertEqual(
                        staged_skill_dir,
                        staged_workspace / ".agents" / "skills" / exact_skill_name,
                    ),
                ),
                (
                    CURRENT_INVENTORY[29],
                    lambda: self.assertTrue(
                        copy_mock.call_count == 0
                        and auth_file.read_text(encoding="utf-8") == "credential sentinel\n"
                        and "auth.json" not in CODEX_ENGINE.read_text(encoding="utf-8")
                    ),
                ),
                (
                    CURRENT_INVENTORY[30],
                    lambda: self.assertEqual(codex_env.get("CODEX_HOME"), str(auth_home)),
                ),
                (
                    CURRENT_INVENTORY[31],
                    lambda: self.assertTrue(
                        codex_rc == 0
                        and codex_stdout == valid_jsonl
                        and codex_stderr == ""
                        and "--sandbox" in codex_command
                        and codex_command[codex_command.index("--sandbox") + 1] == "read-only"
                        and "--ephemeral" in codex_command
                        and "--ignore-user-config" in codex_command
                        and "--json" in codex_command
                        and codex_command[codex_command.index("-m") + 1] == "gpt-5.6-sol"
                        and 'model_reasoning_effort="low"' in codex_command
                    ),
                ),
                (
                    CURRENT_INVENTORY[32],
                    lambda: self.assertTrue(
                        "--ignore-rules" not in codex_command
                        and "--dangerously-bypass-approvals-and-sandbox" not in codex_command
                        and "--full-auto" not in codex_command
                    ),
                ),
                (
                    CURRENT_INVENTORY[33],
                    lambda: self.assertTrue(
                        valid_evidence["valid"]
                        and not missing_lifecycle_evidence["valid"]
                    ),
                ),
                (
                    CURRENT_INVENTORY[34],
                    lambda: self.assertTrue(
                        valid_evidence["valid"] and valid_evidence["selected"]
                    ),
                ),
                (
                    CURRENT_INVENTORY[35],
                    lambda: self.assertEqual(valid_evidence["selected_marker"], exact_marker),
                ),
                (
                    CURRENT_INVENTORY[36],
                    lambda: self.assertTrue(
                        not competing_evidence["valid"]
                        and "competing" in str(competing_evidence["reason"]).lower()
                    ),
                ),
                (
                    CURRENT_INVENTORY[37],
                    lambda: self.assertTrue(
                        not wrong_order_evidence["valid"]
                        and "order" in str(wrong_order_evidence["reason"]).lower()
                    ),
                ),
                (
                    CURRENT_INVENTORY[38],
                    lambda: self.assertTrue(
                        not nested_error_evidence["valid"]
                        and "failed" in str(nested_error_evidence["reason"]).lower()
                    ),
                ),
                (
                    CURRENT_INVENTORY[39],
                    lambda: self.assertTrue(
                        model_evidence["requested_model"] == "gpt-5.6-sol"
                        and model_evidence["resolved_model"] is None
                    ),
                ),
                (
                    CURRENT_INVENTORY[40],
                    lambda: self.assertTrue(
                        Path(str(raw_evidence["jsonl_path"])).read_text(encoding="utf-8") == valid_jsonl
                        and Path(str(raw_evidence["stderr_path"])).read_text(encoding="utf-8")
                        == "provider stderr\n"
                        and raw_evidence["jsonl_sha256"]
                        == hashlib.sha256(valid_jsonl.encode("utf-8")).hexdigest()
                        and raw_evidence["stderr_sha256"]
                        == hashlib.sha256(b"provider stderr\n").hexdigest()
                    ),
                ),
                (CURRENT_INVENTORY[41], lambda: self.assertIsNotNone(cleanup_residue)),
                (
                    CURRENT_INVENTORY[42],
                    lambda: self.assertTrue(
                        invalid_codex_subprocess_calls == 0
                        and len(invalid_codex_messages) == 4
                        and any("JSON list" in message for message in invalid_codex_messages)
                        and any("requires" in message for message in invalid_codex_messages)
                        and sum("could not read" in message for message in invalid_codex_messages) == 2
                    ),
                ),
                (
                    CURRENT_INVENTORY[43],
                    lambda: self.assertFalse(
                        codex_engine.case_passes(False, triggers=0, runs=3, threshold=0.5, invalid_runs=1)
                    ),
                ),
                (
                    CURRENT_INVENTORY[44],
                    lambda: self.assertIn(
                        ["--model", "claude-sonnet-test"],
                        [
                            list(direct_mode_run.call_args.args[0])[index : index + 2]
                            for index in range(len(direct_mode_run.call_args.args[0]) - 1)
                        ],
                    ),
                ),
                (
                    CURRENT_INVENTORY[45],
                    lambda: self.assertTrue(not failed_summary_valid and failed_mode_exit == 1),
                ),
                (CURRENT_INVENTORY[46], lambda: self.assertFalse(incomplete_trials_valid)),
                (CURRENT_INVENTORY[47], lambda: self.assertFalse(duplicate_result_valid)),
                (CURRENT_INVENTORY[48], lambda: self.assertFalse(wrong_polarity_valid)),
                (CURRENT_INVENTORY[49], lambda: self.assertFalse(inconsistent_rate_valid)),
                (
                    CURRENT_INVENTORY[50],
                    lambda: self.assertTrue(
                        malformed_claude_exit == 1 and malformed_claude_run.call_count == 0
                    ),
                ),
                (
                    CURRENT_INVENTORY[51],
                    lambda: self.assertTrue(
                        direct_evidence_record["requested_model"] == "claude-sonnet-test"
                        and direct_evidence_record["resolved_model"] is None
                        and Path(direct_evidence_record["stdout_path"]).is_file()
                        and direct_evidence_record["stdout_sha256"]
                        == hashlib.sha256(
                            Path(direct_evidence_record["stdout_path"]).read_bytes()
                        ).hexdigest()
                    ),
                ),
            ]

            self.assertEqual([name for name, _check in checks], CURRENT_INVENTORY)
            for name, check in checks:
                with self.subTest(msg=name):
                    check()


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Layer2TriggerRunnerTests)
    return run_counted(suite, label="test-trigger-eval-runners")


if __name__ == "__main__":
    raise SystemExit(main())
