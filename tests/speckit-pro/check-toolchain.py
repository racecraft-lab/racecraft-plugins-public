#!/usr/bin/env python3
"""Report and validate local tools used by speckit-pro checks.

This repo-local preflight is standard-library only and preserves its public
modes, summary shape, and exit-code behavior.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SUPPORTED_MODES = {"tests", "shell", "docs", "all"}
HELP_TEXT = """check-toolchain.py - Report and validate local tools used by speckit-pro checks.

Usage:
  python3 tests/speckit-pro/check-toolchain.py --mode tests
  python3 tests/speckit-pro/check-toolchain.py --mode shell
  python3 tests/speckit-pro/check-toolchain.py --mode docs
  python3 tests/speckit-pro/check-toolchain.py --mode all
"""


@dataclass
class Reporter:
    pass_count: int = 0
    fail_count: int = 0

    def pass_(self, label: str, detail: str = "") -> None:
        self.pass_count += 1
        print(f"PASS {label:<28} {detail}")

    def fail(self, label: str, detail: str = "") -> None:
        self.fail_count += 1
        print(f"FAIL {label:<28} {detail}")

    def warn(self, label: str, detail: str = "") -> None:
        print(f"WARN {label:<28} {detail}")

    def info(self, label: str, detail: str = "") -> None:
        print(f"INFO {label:<28} {detail}")

    def finish(self) -> int:
        total = self.pass_count + self.fail_count
        if self.fail_count == 0:
            print(f"\ncheck-toolchain: {self.pass_count}/{total} passed")
            return 0
        print(f"\ncheck-toolchain: {self.pass_count}/{total} passed ({self.fail_count} failed)")
        print(f"toolchain check failed: {self.fail_count} issue(s)", file=sys.stderr)
        return 1


def parse_args(argv: list[str]) -> tuple[int | None, str]:
    mode = "tests"
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--mode":
            if index + 1 >= len(argv) or argv[index + 1] == "":
                print("Missing value for --mode", file=sys.stderr)
                return 2, mode
            mode = argv[index + 1]
            index += 2
        elif arg.startswith("--mode="):
            mode = arg.split("=", 1)[1]
            index += 1
        elif arg in {"-h", "--help"}:
            print(HELP_TEXT, end="")
            return 0, mode
        else:
            print(f"Unknown argument: {arg}", file=sys.stderr)
            return 2, mode

    if mode not in SUPPORTED_MODES:
        print(f"Invalid --mode: {mode}", file=sys.stderr)
        return 2, mode
    return None, mode


def cmd_path(cmd: str) -> str:
    return shutil.which(cmd) or ""


def run_command(tool: str, args: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    if tool == "node":
        argv = [shutil.which("node") or "node", *args]
    elif tool == "pnpm":
        argv = [shutil.which("pnpm") or "pnpm", *args]
    else:
        raise ValueError(f"unsupported command executable: {tool}")
    try:
        return subprocess.run(
            argv,
            input=input_text,
            text=True,
            capture_output=True,
            shell=False,
            check=False,
        )
    except OSError as exc:
        return subprocess.CompletedProcess(
            argv,
            127,
            "",
            f"command invocation failed: {exc.__class__.__name__}: {exc}",
        )


def require_cmd(reporter: Reporter, label: str, cmd: str) -> None:
    path = cmd_path(cmd)
    if path:
        reporter.pass_(label, path)
    else:
        reporter.fail(label, f"required command not found: {cmd}")


def optional_cmd(reporter: Reporter, label: str, cmd: str, note: str) -> None:
    path = cmd_path(cmd)
    if path:
        reporter.info(label, path)
    else:
        reporter.warn(label, f"not found; required only for {note}")


def version_at_least(version: str, min_major: int, min_minor: int) -> bool:
    parts = version.split(".")
    try:
        major = int(parts[0] if parts else "0")
        minor = int(parts[1] if len(parts) > 1 else "0")
    except ValueError:
        return False
    return major > min_major or (major == min_major and minor >= min_minor)


def check_python_runtime(reporter: Reporter) -> None:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 11):
        reporter.pass_("python >= 3.11", f"{version} ({sys.executable})")
    else:
        reporter.fail("python >= 3.11", f"{version}; Python 3.11 or newer is required")


def check_repo_tools(reporter: Reporter, label: str) -> None:
    print(f"speckit-pro toolchain check ({label})")
    check_python_runtime(reporter)
    require_cmd(reporter, "git", "git")

    optional_cmd(reporter, "gh", "gh", "PR creation, review-comment workflows, and live GitHub-backed checks")
    optional_cmd(reporter, "specify", "specify", "installed-plugin Spec Kit workflows")
    optional_cmd(reporter, "claude", "claude", "Claude live eval and integration fixture modes")
    optional_cmd(reporter, "codex", "codex", "Codex trigger and functional eval modes")


def check_test_tools(reporter: Reporter) -> None:
    check_repo_tools(reporter, "tests")


def check_docs_tools(reporter: Reporter) -> None:
    print("speckit-pro toolchain check (docs)")
    require_cmd(reporter, "node", "node")
    require_cmd(reporter, "corepack", "corepack")
    require_cmd(reporter, "pnpm", "pnpm")

    node_path = cmd_path("node")
    if node_path:
        completed = run_command("node", ["--version"])
        node_version = completed.stdout.strip()
        numeric = re.sub(r"^v", "", node_version)
        numeric = re.sub(r"[^0-9.].*$", "", numeric)
        if version_at_least(numeric, 22, 0):
            reporter.pass_("node >= 22", node_version)
        else:
            reporter.fail("node >= 22", f"{node_version or 'unknown'}; expected Node 22 or newer")

    pnpm_path = cmd_path("pnpm")
    if pnpm_path:
        completed = run_command("pnpm", ["--version"])
        pnpm_version = completed.stdout.strip()
        if pnpm_version == "10.25.0":
            reporter.pass_("pnpm version", pnpm_version)
        else:
            reporter.fail("pnpm version", f"{pnpm_version or 'unknown'}; expected 10.25.0")

    package_json = REPO_ROOT / "docs-site" / "package.json"
    if package_json.is_file():
        package_manager = json.loads(package_json.read_text(encoding="utf-8")).get("packageManager", "")
        if package_manager == "pnpm@10.25.0":
            reporter.pass_("docs packageManager", package_manager)
        else:
            reporter.fail("docs packageManager", f"{package_manager or 'missing'}; expected pnpm@10.25.0")

    node_modules = REPO_ROOT / "docs-site" / "node_modules"
    if pnpm_path and node_modules.is_dir():
        completed = run_command(
            "pnpm",
            ["--dir", str(REPO_ROOT / "docs-site"), "exec", "playwright", "--version"],
        )
        if completed.returncode == 0:
            reporter.pass_("playwright package", completed.stdout.strip())
        else:
            reporter.fail("playwright package", "run pnpm --dir docs-site install --frozen-lockfile first")
    else:
        reporter.fail("docs dependencies", "run pnpm --dir docs-site install --frozen-lockfile first")


def main(argv: list[str]) -> int:
    early_exit, mode = parse_args(argv)
    if early_exit is not None:
        return early_exit

    reporter = Reporter()
    if mode == "tests":
        check_test_tools(reporter)
    elif mode == "shell":
        check_repo_tools(reporter, "shell")
    elif mode == "docs":
        check_docs_tools(reporter)
    elif mode == "all":
        check_test_tools(reporter)
        check_docs_tools(reporter)
    return reporter.finish()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
