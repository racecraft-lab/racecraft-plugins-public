#!/usr/bin/env python3
"""Report and validate local tools used by speckit-pro checks.

Python port of ``check-toolchain.sh`` for XPLAT-010 T047. This repo-local
preflight is standard-library only and preserves the predecessor's modes,
summary shape, and exit-code behavior.
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


def run_command(argv: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        input=input_text,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
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


def check_bash(reporter: Reporter) -> None:
    path = cmd_path("bash")
    if not path:
        reporter.fail("bash >= 4.3", "required command not found: bash")
        return
    completed = run_command([path, "--version"])
    first_line = completed.stdout.splitlines()[0] if completed.stdout else ""
    match = re.search(r"version\s+(\d+)\.(\d+)", first_line, flags=re.IGNORECASE)
    if match and (int(match.group(1)), int(match.group(2))) >= (4, 3):
        reporter.pass_("bash >= 4.3", f"{match.group(1)}.{match.group(2)} ({path})")
    else:
        reporter.fail("bash >= 4.3", f"{first_line or 'unknown'}; install a newer Bash before running the shell suite")


def check_jq(reporter: Reporter) -> None:
    path = cmd_path("jq")
    if not path:
        reporter.fail("jq >= 1.6", "required command not found: jq")
        return
    completed = run_command([path, "--version"])
    version = completed.stdout.strip()
    numeric = re.sub(r"^jq-?", "", version)
    numeric = re.sub(r"[^0-9.].*$", "", numeric)
    if not version_at_least(numeric, 1, 6):
        reporter.fail("jq >= 1.6", f"{version or 'unknown'}; install jq 1.6 or newer")
        return
    expression = run_command([path, "-e", ".ok == true"], input_text='{"ok":true}\n')
    if expression.returncode == 0:
        reporter.pass_("jq >= 1.6", f"{version} ({path})")
    else:
        reporter.fail("jq expression", "jq --version succeeded but a minimal expression failed")


def check_sort_version_semantics(reporter: Reporter) -> None:
    path = cmd_path("sort")
    if not path:
        reporter.fail("sort -V", "version sort is required for semver-style plugin sync checks")
        return
    completed = run_command([path, "-V"], input_text="1.10.2\n1.9.10\n")
    lines = completed.stdout.splitlines()
    if completed.returncode == 0 and lines and lines[-1] == "1.10.2":
        reporter.pass_("sort -V", "semver ordering available")
    else:
        newest = lines[-1] if lines else "missing"
        reporter.fail("sort -V", f"expected 1.10.2 > 1.9.10, got {newest}")


def check_checksum_tool(reporter: Reporter) -> None:
    sha256sum = cmd_path("sha256sum")
    shasum = cmd_path("shasum")
    if sha256sum:
        reporter.pass_("sha256", f"sha256sum ({sha256sum})")
    elif shasum:
        reporter.pass_("sha256", f"shasum ({shasum})")
    else:
        reporter.fail("sha256", "sha256sum or shasum is required for packet fingerprints")


def check_yaml_validator(reporter: Reporter) -> None:
    python3 = cmd_path("python3")
    if python3 and run_command([python3, "-c", "import yaml"]).returncode == 0:
        reporter.pass_("yaml validator", "python3 PyYAML")
        return
    ruby = cmd_path("ruby")
    if ruby and run_command([ruby, "-e", "require 'yaml'"]).returncode == 0:
        reporter.pass_("yaml validator", "ruby yaml")
        return
    reporter.fail("yaml validator", "python3 with PyYAML or ruby is required for workflow YAML checks")


def check_shell_tools(reporter: Reporter, label: str) -> None:
    print(f"speckit-pro toolchain check ({label})")
    check_bash(reporter)
    check_jq(reporter)
    require_cmd(reporter, "git", "git")
    require_cmd(reporter, "python3", "python3")

    for command in ("awk", "sed", "grep", "sort", "find", "mktemp", "wc", "head", "tail", "cut", "dirname", "basename", "pwd"):
        require_cmd(reporter, command, command)

    check_sort_version_semantics(reporter)
    check_checksum_tool(reporter)

    optional_cmd(reporter, "gh", "gh", "PR creation, review-comment workflows, and live GitHub-backed checks")
    optional_cmd(reporter, "specify", "specify", "installed-plugin Spec Kit workflows")
    optional_cmd(reporter, "claude", "claude", "Claude live eval and integration fixture modes")
    optional_cmd(reporter, "codex", "codex", "Codex trigger, functional, and efficiency eval modes")


def check_test_tools(reporter: Reporter) -> None:
    check_shell_tools(reporter, "tests")
    check_yaml_validator(reporter)


def check_docs_tools(reporter: Reporter) -> None:
    print("speckit-pro toolchain check (docs)")
    require_cmd(reporter, "node", "node")
    require_cmd(reporter, "corepack", "corepack")
    require_cmd(reporter, "pnpm", "pnpm")

    node_path = cmd_path("node")
    if node_path:
        completed = run_command([node_path, "--version"])
        node_version = completed.stdout.strip()
        numeric = re.sub(r"^v", "", node_version)
        numeric = re.sub(r"[^0-9.].*$", "", numeric)
        if version_at_least(numeric, 22, 0):
            reporter.pass_("node >= 22", node_version)
        else:
            reporter.fail("node >= 22", f"{node_version or 'unknown'}; expected Node 22 or newer")

    pnpm_path = cmd_path("pnpm")
    if pnpm_path:
        completed = run_command([pnpm_path, "--version"])
        pnpm_version = completed.stdout.strip()
        if pnpm_version == "10.25.0":
            reporter.pass_("pnpm version", pnpm_version)
        else:
            reporter.fail("pnpm version", f"{pnpm_version or 'unknown'}; expected 10.25.0")

    package_json = REPO_ROOT / "docs-site" / "package.json"
    if package_json.is_file() and cmd_path("python3"):
        package_manager = json.loads(package_json.read_text(encoding="utf-8")).get("packageManager", "")
        if package_manager == "pnpm@10.25.0":
            reporter.pass_("docs packageManager", package_manager)
        else:
            reporter.fail("docs packageManager", f"{package_manager or 'missing'}; expected pnpm@10.25.0")

    node_modules = REPO_ROOT / "docs-site" / "node_modules"
    if pnpm_path and node_modules.is_dir():
        completed = run_command([pnpm_path, "--dir", str(REPO_ROOT / "docs-site"), "exec", "playwright", "--version"])
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
        check_shell_tools(reporter, "shell")
    elif mode == "docs":
        check_docs_tools(reporter)
    elif mode == "all":
        check_test_tools(reporter)
        check_docs_tools(reporter)
    return reporter.finish()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
