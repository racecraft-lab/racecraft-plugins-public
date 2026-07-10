#!/usr/bin/env python3
"""Termination/restoration contracts for the Layer-2 Claude eval runner."""

from __future__ import annotations

import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
RUNNER_PATH = TESTS_ROOT / "layer2-trigger" / "run-trigger-evals.py"
BASELINE = TESTS_ROOT / "parity" / "bash-to-python" / "test-trigger-signal-restoration-baseline.txt"
SHARED_LIB = TESTS_ROOT / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))

from test_result import run_counted  # noqa: E402


CURRENT_INVENTORY = [
    "baseline inventory is truthful and ordered",
    "in-process SIGTERM maps to exit 143",
    "in-process SIGTERM restores the moved production skill",
    "in-process SIGTERM leaves no eval-disabled backup",
    "POSIX subprocess SIGTERM maps to exit 143",
    "POSIX subprocess SIGTERM restores the moved production skill",
    "termination path emits an explicit restoration diagnostic",
]


def import_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("layer2_signal_runner", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
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


def setup_home(root: Path, skill: str) -> tuple[Path, Path]:
    home = root / "home"
    settings = home / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(
        json.dumps({"enabledPlugins": {"speckit-pro@test-marketplace": True}}) + "\n",
        encoding="utf-8",
    )
    production = home / ".claude" / "plugins" / "marketplaces" / "test-marketplace" / "speckit-pro" / "skills" / skill
    production.mkdir(parents=True)
    (production / "marker.txt").write_text("production\n", encoding="utf-8")
    return home, production


class Layer2SignalRestorationTests(unittest.TestCase):
    def test_signal_restoration_contract(self) -> None:
        runner = import_runner()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home, production = setup_home(root / "in-process", "demo")
            plugin_root = root / "plugin"
            (plugin_root / "skills" / "demo").mkdir(parents=True)
            eval_file = plugin_root.parent / "tests" / "speckit-pro" / "layer2-trigger" / "evals" / "demo-trigger.json"
            eval_file.parent.mkdir(parents=True)
            eval_file.write_text("{}\n", encoding="utf-8")
            skill_creator = root / "skill-creator"
            skill_creator.mkdir()
            runner.PLUGIN_ROOT = plugin_root
            stderr = []

            def terminate_from_subprocess(*_args: object, **_kwargs: object) -> object:
                runner.handle_termination(int(signal.SIGTERM), None)
                raise AssertionError("termination handler must raise")

            with (
                mock.patch.dict(
                    os.environ,
                    {"HOME": str(home), "SKILL_CREATOR_ROOT": str(skill_creator)},
                    clear=False,
                ),
                mock.patch.object(runner, "eprint", side_effect=lambda message="": stderr.append(message)),
                mock.patch.object(runner.subprocess, "run", side_effect=terminate_from_subprocess),
            ):
                in_process_exit = runner.main(["demo"])

            in_process_restored = (production / "marker.txt").read_text(encoding="utf-8") == "production\n"
            in_process_backups = list(production.parent.glob("demo.eval-disabled-*"))

            subprocess_exit = 143
            subprocess_restored = True
            subprocess_diagnostic = True
            if os.name != "nt":
                external_root = root / "subprocess"
                external_home, external_production = setup_home(external_root, "speckit-coach")
                external_creator = external_root / "skill-creator"
                scripts = external_creator / "scripts"
                scripts.mkdir(parents=True)
                (scripts / "__init__.py").write_text("", encoding="utf-8")
                marker = external_root / "child-started"
                (scripts / "run_eval.py").write_text(
                    "import os, time\n"
                    "from pathlib import Path\n"
                    "Path(os.environ['L2_SIGNAL_MARKER']).write_text('started\\n', encoding='utf-8')\n"
                    "time.sleep(60)\n",
                    encoding="utf-8",
                )
                env = os.environ.copy()
                env.update(
                    {
                        "HOME": str(external_home),
                        "SKILL_CREATOR_ROOT": str(external_creator),
                        "L2_SIGNAL_MARKER": str(marker),
                        "PYTHONDONTWRITEBYTECODE": "1",
                    }
                )
                process = subprocess.Popen(
                    [sys.executable, str(RUNNER_PATH), "speckit-coach"],
                    cwd=REPO_ROOT,
                    text=True,
                    encoding="utf-8",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    start_new_session=True,
                )
                try:
                    deadline = time.monotonic() + 10
                    while not marker.is_file() and process.poll() is None and time.monotonic() < deadline:
                        time.sleep(0.05)
                    self.assertTrue(marker.is_file(), "blocking eval subprocess did not start")
                    os.killpg(process.pid, signal.SIGTERM)
                    _stdout, external_stderr = process.communicate(timeout=10)
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=5)
                subprocess_exit = int(process.returncode)
                subprocess_restored = (external_production / "marker.txt").is_file()
                subprocess_diagnostic = "restoring moved paths before exit" in external_stderr

            checks = [
                (CURRENT_INVENTORY[0], lambda: self.assertEqual(baseline_inventory(BASELINE), CURRENT_INVENTORY)),
                (CURRENT_INVENTORY[1], lambda: self.assertEqual(in_process_exit, 143)),
                (CURRENT_INVENTORY[2], lambda: self.assertTrue(in_process_restored)),
                (CURRENT_INVENTORY[3], lambda: self.assertEqual(in_process_backups, [])),
                (CURRENT_INVENTORY[4], lambda: self.assertEqual(subprocess_exit, 143)),
                (CURRENT_INVENTORY[5], lambda: self.assertTrue(subprocess_restored)),
                (
                    CURRENT_INVENTORY[6],
                    lambda: self.assertTrue(
                        any("restoring moved paths before exit" in line for line in stderr)
                        and subprocess_diagnostic
                    ),
                ),
            ]

            self.assertEqual([name for name, _check in checks], CURRENT_INVENTORY)
            for name, check in checks:
                with self.subTest(msg=name):
                    check()


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Layer2SignalRestorationTests)
    raise SystemExit(run_counted(suite, label="test-trigger-signal-restoration"))
