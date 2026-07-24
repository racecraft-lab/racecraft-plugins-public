#!/usr/bin/env python3
"""Layer-4 contract for the terminal Python-only toolchain preflight."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
CHECKER = REPO_ROOT / "tests" / "speckit-pro" / "check-toolchain.py"
BASELINE = REPO_ROOT / "tests" / "speckit-pro" / "parity" / "bash-to-python" / "test-check-toolchain-baseline.txt"

PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for path in (PLUGIN_ROOT, LIB_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
from speckit_pro_runner.gates.active_path_guard import repo_bash_python_findings  # noqa: E402
from capture_baseline import baseline_inventory  # noqa: E402
from test_result import run_counted  # noqa: E402


CURRENT_INVENTORY = [
    "toolchain checker exists",
    "toolchain checker is executable",
    "help exits 0",
    "help lists supported modes",
    "help describes the Python entrypoint",
    "default tests mode exits 0",
    "default tests mode prints summary",
    "default tests mode labels output",
    "default tests mode validates the current Python runtime",
    "default tests mode requires git",
    "default tests mode does not require Bash",
    "default tests mode does not require jq",
    "shell compatibility mode exits 0",
    "shell compatibility mode labels output",
    "shell compatibility mode does not require Bash",
    "shell compatibility mode does not require jq",
    "missing --mode value exits 2",
    "missing --mode value prints a diagnostic",
    "invalid --mode value exits 2",
    "invalid --mode value prints a diagnostic",
    "unknown argument exits 2",
    "missing git exits 1",
    "missing git prints diagnostic",
    "missing git still prints summary",
    "toolchain source has no forbidden command resolution",
    "shell compatibility mode passes with a git-only PATH",
    "docs mode scores command launch OSError",
]


def run_checker(*args: str, path_fixture: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if path_fixture is not None:
        env["PATH"] = str(path_fixture)
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=env,
        shell=False,
        check=False,
    )


def merged_output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def write_git_marker(path_fixture: Path) -> None:
    path_fixture.mkdir(parents=True, exist_ok=True)
    marker = path_fixture / ("git.exe" if os.name == "nt" else "git")
    marker.write_bytes(b"")
    marker.chmod(0o755)


def forbidden_command_resolution(path: Path) -> list[str]:
    return [
        f"{finding.line}: {finding.pattern}"
        for finding in repo_bash_python_findings(
            str(path.relative_to(REPO_ROOT)),
            path.read_text(encoding="utf-8"),
        )
    ]


def assert_source_is_python_only(test: unittest.TestCase) -> None:
    source = CHECKER.read_text(encoding="utf-8")
    test.assertEqual(forbidden_command_resolution(CHECKER), [])
    test.assertNotIn('package_json.is_file() and cmd_path("python3")', source)


def import_checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_toolchain_under_test", CHECKER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def assert_oserror_is_scored_by_real_main(test: unittest.TestCase) -> None:
    module = import_checker()
    stdout = io.StringIO()
    stderr = io.StringIO()
    with (
        mock.patch.object(module, "cmd_path", return_value="/fixture/tool"),
        mock.patch.object(module.subprocess, "run", side_effect=OSError("exec format error")),
        contextlib.redirect_stdout(stdout),
        contextlib.redirect_stderr(stderr),
    ):
        exit_code = module.main(["--mode", "docs"])
    output = stdout.getvalue() + stderr.getvalue()
    test.assertEqual(exit_code, 1)
    test.assertIn("check-toolchain:", output)
    test.assertIn("failed", output)


class CheckToolchainTests(unittest.TestCase):
    def test_toolchain_checker_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            empty_path = root / "empty"
            empty_path.mkdir()
            git_only_path = root / "git-only"
            write_git_marker(git_only_path)

            help_result = run_checker("--help")
            default_result = run_checker()
            shell_result = run_checker("--mode", "shell")
            missing_mode = run_checker("--mode")
            invalid_mode = run_checker("--mode", "invalid")
            unknown = run_checker("--bogus")
            missing_git = run_checker(path_fixture=empty_path)
            git_only = run_checker("--mode", "shell", path_fixture=git_only_path)

            help_output = merged_output(help_result)
            default_output = merged_output(default_result)
            shell_output = merged_output(shell_result)
            missing_git_output = merged_output(missing_git)

            self.assertEqual(baseline_inventory(BASELINE), CURRENT_INVENTORY)
            checks = [
                (CURRENT_INVENTORY[0], lambda: self.assertTrue(CHECKER.is_file())),
                (CURRENT_INVENTORY[1], lambda: self.assertTrue(os.access(CHECKER, os.X_OK))),
                (CURRENT_INVENTORY[2], lambda: self.assertEqual(help_result.returncode, 0, help_output)),
                (CURRENT_INVENTORY[3], lambda: self.assertIn("--mode all", help_output)),
                (CURRENT_INVENTORY[4], lambda: self.assertIn("python3 tests/speckit-pro/check-toolchain.py", help_output)),
                (CURRENT_INVENTORY[5], lambda: self.assertEqual(default_result.returncode, 0, default_output)),
                (CURRENT_INVENTORY[6], lambda: self.assertIn("check-toolchain:", default_output)),
                (CURRENT_INVENTORY[7], lambda: self.assertIn("toolchain check (tests)", default_output)),
                (CURRENT_INVENTORY[8], lambda: self.assertIn("PASS python >= 3.11", default_output)),
                (CURRENT_INVENTORY[9], lambda: self.assertIn("PASS git", default_output)),
                (CURRENT_INVENTORY[10], lambda: self.assertNotIn("pass bash", default_output.lower())),
                (CURRENT_INVENTORY[11], lambda: self.assertNotIn("pass jq", default_output.lower())),
                (CURRENT_INVENTORY[12], lambda: self.assertEqual(shell_result.returncode, 0, shell_output)),
                (CURRENT_INVENTORY[13], lambda: self.assertIn("toolchain check (shell)", shell_output)),
                (CURRENT_INVENTORY[14], lambda: self.assertNotIn("pass bash", shell_output.lower())),
                (CURRENT_INVENTORY[15], lambda: self.assertNotIn("pass jq", shell_output.lower())),
                (CURRENT_INVENTORY[16], lambda: self.assertEqual(missing_mode.returncode, 2)),
                (CURRENT_INVENTORY[17], lambda: self.assertIn("Missing value for --mode", merged_output(missing_mode))),
                (CURRENT_INVENTORY[18], lambda: self.assertEqual(invalid_mode.returncode, 2)),
                (CURRENT_INVENTORY[19], lambda: self.assertIn("Invalid --mode: invalid", merged_output(invalid_mode))),
                (CURRENT_INVENTORY[20], lambda: self.assertEqual(unknown.returncode, 2)),
                (CURRENT_INVENTORY[21], lambda: self.assertEqual(missing_git.returncode, 1, missing_git_output)),
                (CURRENT_INVENTORY[22], lambda: self.assertIn("required command not found: git", missing_git_output)),
                (CURRENT_INVENTORY[23], lambda: self.assertIn("check-toolchain:", missing_git_output)),
                (CURRENT_INVENTORY[24], lambda: assert_source_is_python_only(self)),
                (CURRENT_INVENTORY[25], lambda: self.assertEqual(git_only.returncode, 0, merged_output(git_only))),
                (CURRENT_INVENTORY[26], lambda: assert_oserror_is_scored_by_real_main(self)),
            ]

            self.assertEqual([name for name, _check in checks], CURRENT_INVENTORY)
            for name, check in checks:
                with self.subTest(msg=name):
                    check()


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CheckToolchainTests)
    return run_counted(suite, label="test-check-toolchain")


if __name__ == "__main__":
    raise SystemExit(main())
