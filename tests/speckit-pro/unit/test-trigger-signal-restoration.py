#!/usr/bin/env python3
"""Termination and owned-resource cleanup contracts for Claude Layer 2 evals."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from types import ModuleType
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
RUNNER_PATH = TESTS_ROOT / "layer2-trigger" / "run-trigger-evals.py"
SHARED_LIB = TESTS_ROOT / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))

from test_result import run_counted  # noqa: E402


CURRENT_INVENTORY = [
    "in-process SIGTERM maps to exit 143",
    "in-process SIGTERM removes the disposable plugin",
    "in-process SIGTERM leaves global state untouched",
    "POSIX subprocess SIGTERM maps to exit 143",
    "POSIX subprocess SIGTERM terminates its owned child and removes its plugin",
    "termination path emits an explicit owned-cleanup diagnostic",
]


def import_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("layer2_signal_runner", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fixture_plugin(root: Path, skill: str) -> Path:
    plugin_root = root / "speckit-pro"
    source = plugin_root / "skills" / skill / "SKILL.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        f"---\nname: {skill}\ndescription: Signal fixture.\n---\n\nBody.\n",
        encoding="utf-8",
    )
    corpus = root / "tests" / "speckit-pro" / "layer2-trigger" / "evals" / f"{skill}-trigger.json"
    corpus.parent.mkdir(parents=True)
    corpus.write_text(
        json.dumps([{"query": "Run the fixture.", "should_trigger": True}]) + "\n",
        encoding="utf-8",
    )
    return plugin_root


def write_blocking_claude(binary_dir: Path) -> Path:
    binary_dir.mkdir(parents=True)
    script = binary_dir / "claude-stub.py"
    script.write_text(
        "import json, os, signal, sys, time\n"
        "from pathlib import Path\n"
        "if '--version' in sys.argv:\n"
        "    print('2.1.261')\n"
        "elif '--help' in sys.argv:\n"
        "    print('--restricted --plugin-dir --strict-mcp-config --mcp-config --tools --allowedTools --output-format --verbose --no-session-persistence')\n"
        "else:\n"
        "    root = sys.argv[sys.argv.index('--plugin-dir') + 1]\n"
        "    Path(os.environ['L2_CHILD_STATE']).write_text(json.dumps({'pid': os.getpid(), 'plugin_root': root}), encoding='utf-8')\n"
        "    def stop(_signum, _frame):\n"
        "        Path(os.environ['L2_CHILD_STOPPED']).write_text('stopped\\n', encoding='utf-8')\n"
        "        raise SystemExit(143)\n"
        "    signal.signal(signal.SIGTERM, stop)\n"
        "    time.sleep(60)\n",
        encoding="utf-8",
    )
    launcher = binary_dir / "claude"
    launcher.write_text(
        f"#!{sys.executable}\nimport runpy\nrunpy.run_path({str(script)!r}, run_name='__main__')\n",
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    return launcher


class Layer2SignalRestorationTests(unittest.TestCase):
    def test_signal_cleanup_contract(self) -> None:
        runner = import_runner()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture_root = root / "in-process-fixture"
            runner.PLUGIN_ROOT = fixture_plugin(fixture_root, "demo")
            staged_root = root / "in-process-staged"
            staged_root.mkdir()
            evidence_root = root / "in-process-evidence"
            evidence_root.mkdir()
            global_sentinel = root / "home" / ".claude" / "sentinel"
            global_sentinel.parent.mkdir(parents=True)
            global_sentinel.write_text("untouched\n", encoding="utf-8")
            diagnostics: list[str] = []

            def terminate(*_args: object, **_kwargs: object) -> object:
                runner.handle_termination(int(signal.SIGTERM), None)
                raise AssertionError("termination handler must raise")

            with (
                mock.patch.dict(os.environ, {"HOME": str(global_sentinel.parents[1])}, clear=False),
                mock.patch.object(runner.shutil, "which", return_value="/usr/local/bin/claude"),
                mock.patch.object(
                    runner,
                    "cli_preflight",
                    return_value=({"version": "2.1.261", "supported_flags": []}, "ok"),
                ),
                mock.patch.object(runner.tempfile, "mkdtemp", side_effect=[str(staged_root), str(evidence_root)]),
                mock.patch.object(runner, "run_claude_query", side_effect=terminate),
                mock.patch.object(runner, "eprint", side_effect=lambda message="": diagnostics.append(message)),
            ):
                in_process_exit = runner.main(["demo"])

            subprocess_exit = 143
            subprocess_clean = True
            subprocess_diagnostic = True
            if os.name != "nt":
                external_root = root / "external"
                binary_dir = external_root / "bin"
                write_blocking_claude(binary_dir)
                child_state = external_root / "child-state.json"
                child_stopped = external_root / "child-stopped"
                external_home = external_root / "home"
                external_sentinel = external_home / ".claude" / "sentinel"
                external_sentinel.parent.mkdir(parents=True)
                external_sentinel.write_text("untouched\n", encoding="utf-8")
                evidence = external_root / "evidence"
                env = os.environ.copy()
                env.update(
                    {
                        "HOME": str(external_home),
                        "PATH": f"{binary_dir}{os.pathsep}{env.get('PATH', '')}",
                        "L2_CHILD_STATE": str(child_state),
                        "L2_CHILD_STOPPED": str(child_stopped),
                        "PYTHONDONTWRITEBYTECODE": "1",
                    }
                )
                process = subprocess.Popen(
                    [sys.executable, str(RUNNER_PATH), "speckit-coach", "--evidence-dir", str(evidence)],
                    cwd=REPO_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    start_new_session=True,
                )
                try:
                    deadline = time.monotonic() + 10
                    while not child_state.is_file() and process.poll() is None and time.monotonic() < deadline:
                        time.sleep(0.05)
                    self.assertTrue(child_state.is_file(), "blocking owned child did not start")
                    state = json.loads(child_state.read_text(encoding="utf-8"))
                    os.kill(process.pid, signal.SIGTERM)
                    _stdout, external_stderr = process.communicate(timeout=10)
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=5)
                subprocess_exit = int(process.returncode)
                subprocess_clean = (
                    child_stopped.is_file()
                    and not Path(state["plugin_root"]).exists()
                    and external_sentinel.read_text(encoding="utf-8") == "untouched\n"
                )
                subprocess_diagnostic = "terminating owned child and cleaning temporary plugin" in external_stderr

            checks = [
                lambda: self.assertEqual(in_process_exit, 143),
                lambda: self.assertFalse(staged_root.exists()),
                lambda: self.assertEqual(global_sentinel.read_text(encoding="utf-8"), "untouched\n"),
                lambda: self.assertEqual(subprocess_exit, 143),
                lambda: self.assertTrue(subprocess_clean),
                lambda: self.assertTrue(
                    any("terminating owned child and cleaning temporary plugin" in line for line in diagnostics)
                    and subprocess_diagnostic
                ),
            ]
            for name, check in zip(CURRENT_INVENTORY, checks, strict=True):
                with self.subTest(msg=name):
                    check()


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Layer2SignalRestorationTests)
    raise SystemExit(run_counted(suite, label="test-trigger-signal-restoration"))
