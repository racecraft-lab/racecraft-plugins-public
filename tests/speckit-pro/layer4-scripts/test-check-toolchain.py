#!/usr/bin/env python3
"""Count-parity contract for the transitional Python toolchain checker."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CHECKER = REPO_ROOT / "tests" / "speckit-pro" / "check-toolchain.py"
BASELINE = REPO_ROOT / "tests" / "speckit-pro" / "parity" / "xplat-010" / "test-check-toolchain-baseline.txt"

LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


CURRENT_INVENTORY = [
    "toolchain checker exists",
    "toolchain checker is executable",
    "help exits 0",
    "help lists supported modes",
    "help does not include shell code",
    "default tests mode exits 0",
    "default tests mode prints summary",
    "shell mode exits 0",
    "shell mode labels output",
    "missing --mode value exits 2",
    "missing --mode value prints a diagnostic",
    "invalid --mode value exits 2",
    "invalid --mode value prints a diagnostic",
    "unknown argument exits 2",
    "missing jq exits 1",
    "missing jq prints diagnostic",
    "missing jq still prints summary",
    "broken jq expression exits 1",
    "broken jq expression prints diagnostic",
    "too-old jq exits 1",
    "too-old jq prints diagnostic",
    "missing python3 exits 1",
    "missing python3 prints diagnostic",
    "tests mode fails without YAML validator",
    "tests mode reports missing YAML validator",
    "shell mode does not require YAML validator",
]

FIXTURE_COMMANDS = (
    "bash",
    "awk",
    "sed",
    "grep",
    "sort",
    "find",
    "mktemp",
    "wc",
    "head",
    "tail",
    "cut",
    "dirname",
    "basename",
    "pwd",
    "git",
    "python3",
    "jq",
    "sha256sum",
    "shasum",
    "ruby",
)


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


def fixture_name(command: str, source: str | None = None) -> str:
    if os.name == "nt" and source and Path(source).suffix.lower() in {".exe", ".cmd", ".bat"}:
        return f"{command}{Path(source).suffix.lower()}"
    return command


def link_or_copy(source: str, destination: Path) -> None:
    try:
        destination.symlink_to(source)
    except OSError:
        shutil.copy2(source, destination)


def make_path_fixture(root: Path, name: str, omit: str = "") -> Path:
    bin_dir = root / name
    bin_dir.mkdir()
    for command in FIXTURE_COMMANDS:
        if command == omit:
            continue
        source = shutil.which(command)
        if source:
            link_or_copy(source, bin_dir / fixture_name(command, source))
    return bin_dir


def write_python_executable(path: Path, body: str) -> None:
    path.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
    path.chmod(0o755)


def remove_command(bin_dir: Path, command: str) -> None:
    for candidate in bin_dir.glob(f"{command}*"):
        candidate.unlink()


def write_fake_python_without_yaml(bin_dir: Path) -> None:
    remove_command(bin_dir, "python3")
    write_python_executable(
        bin_dir / fixture_name("python3", sys.executable),
        "import sys\nraise SystemExit(1 if len(sys.argv) > 2 and sys.argv[1] == '-c' and 'import yaml' in sys.argv[2] else 0)\n",
    )


def write_fake_jq(bin_dir: Path, version: str, expression_exit: int) -> None:
    remove_command(bin_dir, "jq")
    write_python_executable(
        bin_dir / fixture_name("jq", sys.executable),
        f"import sys\nprint({version!r}) if len(sys.argv) > 1 and sys.argv[1] == '--version' else None\n"
        f"raise SystemExit(0 if len(sys.argv) > 1 and sys.argv[1] == '--version' else {expression_exit})\n",
    )


class CheckToolchainTests(unittest.TestCase):
    def test_toolchain_checker_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missing_jq_path = make_path_fixture(root, "missing-jq", "jq")
            broken_jq_path = make_path_fixture(root, "broken-jq", "jq")
            write_fake_jq(broken_jq_path, "jq-1.7", 2)
            old_jq_path = make_path_fixture(root, "old-jq", "jq")
            write_fake_jq(old_jq_path, "jq-1.5", 0)
            missing_python_path = make_path_fixture(root, "missing-python", "python3")
            missing_yaml_path = make_path_fixture(root, "missing-yaml", "python3")
            remove_command(missing_yaml_path, "ruby")
            write_fake_python_without_yaml(missing_yaml_path)

            help_result = run_checker("--help")
            default_result = run_checker()
            shell_result = run_checker("--mode", "shell")
            missing_mode = run_checker("--mode")
            invalid_mode = run_checker("--mode", "invalid")
            unknown = run_checker("--bogus")
            missing_jq = run_checker(path_fixture=missing_jq_path)
            broken_jq = run_checker(path_fixture=broken_jq_path)
            old_jq = run_checker(path_fixture=old_jq_path)
            missing_python = run_checker(path_fixture=missing_python_path)
            missing_yaml_tests = run_checker("--mode", "tests", path_fixture=missing_yaml_path)
            missing_yaml_shell = run_checker("--mode", "shell", path_fixture=missing_yaml_path)

            help_output = merged_output(help_result)
            default_output = merged_output(default_result)
            shell_output = merged_output(shell_result)
            missing_jq_output = merged_output(missing_jq)
            broken_jq_output = merged_output(broken_jq)
            old_jq_output = merged_output(old_jq)
            missing_python_output = merged_output(missing_python)
            missing_yaml_output = merged_output(missing_yaml_tests)

            self.assertEqual(baseline_inventory(BASELINE), CURRENT_INVENTORY)
            checks = [
                (CURRENT_INVENTORY[0], lambda: self.assertTrue(CHECKER.is_file())),
                (CURRENT_INVENTORY[1], lambda: self.assertTrue(os.access(CHECKER, os.X_OK))),
                (CURRENT_INVENTORY[2], lambda: self.assertEqual(help_result.returncode, 0, help_output)),
                (CURRENT_INVENTORY[3], lambda: self.assertIn("--mode all", help_output)),
                (CURRENT_INVENTORY[4], lambda: self.assertNotIn("set -euo pipefail", help_output)),
                (CURRENT_INVENTORY[5], lambda: self.assertEqual(default_result.returncode, 0, default_output)),
                (CURRENT_INVENTORY[6], lambda: self.assertIn("check-toolchain:", default_output)),
                (CURRENT_INVENTORY[7], lambda: self.assertEqual(shell_result.returncode, 0, shell_output)),
                (CURRENT_INVENTORY[8], lambda: self.assertIn("speckit-pro toolchain check (shell)", shell_output)),
                (CURRENT_INVENTORY[9], lambda: self.assertEqual(missing_mode.returncode, 2)),
                (CURRENT_INVENTORY[10], lambda: self.assertIn("Missing value for --mode", merged_output(missing_mode))),
                (CURRENT_INVENTORY[11], lambda: self.assertEqual(invalid_mode.returncode, 2)),
                (CURRENT_INVENTORY[12], lambda: self.assertIn("Invalid --mode: invalid", merged_output(invalid_mode))),
                (CURRENT_INVENTORY[13], lambda: self.assertEqual(unknown.returncode, 2)),
                (CURRENT_INVENTORY[14], lambda: self.assertEqual(missing_jq.returncode, 1, missing_jq_output)),
                (CURRENT_INVENTORY[15], lambda: self.assertIn("required command not found: jq", missing_jq_output)),
                (CURRENT_INVENTORY[16], lambda: self.assertIn("check-toolchain:", missing_jq_output)),
                (CURRENT_INVENTORY[17], lambda: self.assertEqual(broken_jq.returncode, 1, broken_jq_output)),
                (CURRENT_INVENTORY[18], lambda: self.assertIn("jq expression", broken_jq_output)),
                (CURRENT_INVENTORY[19], lambda: self.assertEqual(old_jq.returncode, 1, old_jq_output)),
                (CURRENT_INVENTORY[20], lambda: self.assertIn("install jq 1.6 or newer", old_jq_output)),
                (CURRENT_INVENTORY[21], lambda: self.assertEqual(missing_python.returncode, 1, missing_python_output)),
                (CURRENT_INVENTORY[22], lambda: self.assertIn("required command not found: python3", missing_python_output)),
                (CURRENT_INVENTORY[23], lambda: self.assertEqual(missing_yaml_tests.returncode, 1, missing_yaml_output)),
                (CURRENT_INVENTORY[24], lambda: self.assertIn("yaml validator", missing_yaml_output)),
                (CURRENT_INVENTORY[25], lambda: self.assertEqual(missing_yaml_shell.returncode, 0, merged_output(missing_yaml_shell))),
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
