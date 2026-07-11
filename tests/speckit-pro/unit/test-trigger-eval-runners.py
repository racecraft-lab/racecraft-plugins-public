#!/usr/bin/env python3
"""Deterministic Layer-4 contracts for the Python Layer-2 trigger runners."""

from __future__ import annotations

import ast
from contextlib import redirect_stderr
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
LOOP_RUNNER = LAYER2 / "run-trigger-loop.py"
BASELINE = TESTS_ROOT / "parity" / "bash-to-python" / "test-trigger-eval-runners-baseline.txt"
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


def baseline_inventory(path: Path) -> list[str]:
    names: list[str] = []
    total: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("TOTAL: "):
            total = int(line.removeprefix("TOTAL: "))
            continue
        _ordinal, name = line.split(" ", 1)
        names.append(name)
    if total != len(names):
        raise AssertionError(f"baseline TOTAL {total} does not match {len(names)} names")
    return names


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
        loop = import_script(LOOP_RUNNER, "xplat010_layer2_loop_runner")
        source_paths = (CLAUDE_RUNNER, CODEX_RUNNER, LOOP_RUNNER)

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
            claude_eval.write_text("{}\n", encoding="utf-8")
            claude.PLUGIN_ROOT = claude_plugin_root
            fake_home = root / "fake-home"
            fake_home.mkdir()
            skill_creator = root / "claude-skill-creator"
            skill_creator.mkdir()

            settings_only_stderr = io.StringIO()
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
                    return_value=SimpleNamespace(returncode=0),
                ) as settings_only_run,
                mock.patch.object(claude, "write_claude_wrapper", wraps=claude.write_claude_wrapper) as settings_wrap,
                redirect_stderr(settings_only_stderr),
            ):
                settings_only_exit = claude.main(["demo"])

            direct_mode_stderr = io.StringIO()
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
                    return_value=SimpleNamespace(returncode=0),
                ) as direct_mode_run,
                mock.patch.object(claude, "write_claude_wrapper", wraps=claude.write_claude_wrapper) as direct_wrap,
                redirect_stderr(direct_mode_stderr),
            ):
                direct_mode_exit = claude.main(["demo"])

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

            self.assertEqual(baseline_inventory(BASELINE), CURRENT_INVENTORY)
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
