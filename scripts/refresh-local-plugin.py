#!/usr/bin/env python3
"""Maintainer helper for local plugin payload refresh."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

PLUGIN_NAME = os.environ.get("SPECKIT_PLUGIN_NAME", "speckit-pro")
MARKETPLACE = os.environ.get("SPECKIT_MARKETPLACE", "racecraft-plugins-public")
CLAUDE_SCOPE = "user"

RUN_BUILD = True
RUN_VALIDATE = True
RUN_CODEX = True
RUN_CLAUDE_INSTALL = True
RUN_CLAUDE_LAUNCH = False
DRY_RUN = False


USAGE = """Usage: scripts/refresh-local-plugin.py [options]

Rebuild generated plugin payloads and refresh the local Claude Code and Codex
installed-plugin caches for maintainer dogfooding.

Default:
  Rebuild dist payloads, validate the Claude payload, refresh both the Claude
  Code and Codex installed-plugin caches, and print the recommended Claude Code
  local-development command:

    claude --plugin-dir dist/claude/speckit-pro

Options:
  --all                Refresh Codex and Claude installed-plugin caches (default).
  --codex              Refresh the Codex installed plugin via remove/add (default).
  --claude-install     Refresh Claude Code's installed plugin cache (default).
  --no-codex           Skip the Codex installed-plugin cache refresh.
  --no-claude-install  Skip Claude Code's installed-plugin cache refresh.
  --launch-claude      Launch Claude Code with --plugin-dir for this session.
  --scope SCOPE        Claude install scope: user, project, or local. Default: user.
  --no-build           Skip payload rebuild.
  --no-validate        Skip Claude payload validation.
  --dry-run            Print commands without running them.
  -h, --help           Show this help.

Environment:
  SPECKIT_PLUGIN_NAME   Plugin name. Default: speckit-pro
  SPECKIT_MARKETPLACE   Marketplace name. Default: racecraft-plugins-public
"""


class UsageError(Exception):
    """Usage error with exit code 2."""


class FatalError(Exception):
    """Runtime error with exit code 1."""


def die(message: str) -> None:
    raise FatalError(message)


def usage_error(message: str) -> None:
    raise UsageError(message)


def quote_args(args: list[str]) -> str:
    return "".join(f" {shlex.quote(str(arg))}" for arg in args)


def print_cmd(args: list[str]) -> None:
    print(f"+{quote_args(args)}")


def run_known_command(
    args: list[str],
    *,
    cwd: Path | None = None,
    capture_output: bool = False,
    check: bool,
) -> subprocess.CompletedProcess[str]:
    if not args:
        raise FatalError("command argv must not be empty")

    executable, *tail = args
    if executable == "claude":
        return subprocess.run(
            ["claude", *tail],
            cwd=cwd,
            text=True,
            capture_output=capture_output,
            shell=False,
            check=check,
        )
    if executable == "codex":
        return subprocess.run(
            ["codex", *tail],
            cwd=cwd,
            text=True,
            capture_output=capture_output,
            shell=False,
            check=check,
        )
    if executable == sys.executable:
        return subprocess.run(
            [sys.executable, *tail],
            cwd=cwd,
            text=True,
            capture_output=capture_output,
            shell=False,
            check=check,
        )
    raise FatalError(f"unsupported command executable: {executable}")


def run_cmd(args: list[str]) -> subprocess.CompletedProcess[str] | None:
    if DRY_RUN:
        print_cmd(args)
        return None
    return run_known_command(args, check=True)


def run_in_repo(args: list[str]) -> subprocess.CompletedProcess[str] | None:
    if DRY_RUN:
        print(f"+ cd {shlex.quote(str(REPO_ROOT))} &&{quote_args(args)}")
        return None
    return run_known_command(args, cwd=REPO_ROOT, check=True)


def require_cmd(name: str) -> None:
    if DRY_RUN:
        return
    if shutil.which(name) is None:
        die(f"required command not found: {name}")


def plugin_selector() -> str:
    return f"{PLUGIN_NAME}@{MARKETPLACE}"


def claude_payload_dir() -> Path:
    return REPO_ROOT / "dist" / "claude" / PLUGIN_NAME


def codex_payload_dir() -> Path:
    return REPO_ROOT / "dist" / "codex" / PLUGIN_NAME


def claude_dev_command() -> str:
    return f"claude --plugin-dir {shlex.quote(str(claude_payload_dir()))}"


def parse_args(argv: list[str]) -> None:
    global CLAUDE_SCOPE, RUN_BUILD, RUN_VALIDATE, RUN_CODEX
    global RUN_CLAUDE_INSTALL, RUN_CLAUDE_LAUNCH, DRY_RUN

    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--all":
            RUN_CODEX = True
            RUN_CLAUDE_INSTALL = True
        elif arg == "--codex":
            RUN_CODEX = True
        elif arg == "--claude-install":
            RUN_CLAUDE_INSTALL = True
        elif arg == "--no-codex":
            RUN_CODEX = False
        elif arg == "--no-claude-install":
            RUN_CLAUDE_INSTALL = False
        elif arg == "--launch-claude":
            RUN_CLAUDE_LAUNCH = True
        elif arg == "--scope":
            index += 1
            if index >= len(argv):
                usage_error("--scope requires a value")
            CLAUDE_SCOPE = argv[index]
        elif arg.startswith("--scope="):
            CLAUDE_SCOPE = arg.split("=", 1)[1]
        elif arg == "--no-build":
            RUN_BUILD = False
        elif arg == "--no-validate":
            RUN_VALIDATE = False
        elif arg == "--dry-run":
            DRY_RUN = True
        elif arg in {"-h", "--help"}:
            print(USAGE, end="")
            raise SystemExit(0)
        else:
            usage_error(f"unknown option: {arg}")
        index += 1

    if CLAUDE_SCOPE not in {"user", "project", "local"}:
        usage_error("--scope must be one of: user, project, local")


def validate_layout() -> None:
    if not (REPO_ROOT / "scripts" / "build-plugin-payloads.py").is_file():
        die(f"payload builder not found: {REPO_ROOT / 'scripts' / 'build-plugin-payloads.py'}")

    if not RUN_BUILD and not DRY_RUN:
        if not claude_payload_dir().is_dir():
            die(f"Claude payload not found: {claude_payload_dir()}")
        if not codex_payload_dir().is_dir():
            die(f"Codex payload not found: {codex_payload_dir()}")


def build_payloads() -> None:
    print("==> Building generated Claude and Codex payloads ...")
    run_in_repo([sys.executable, "scripts/build-plugin-payloads.py"])


def validate_claude_payload() -> None:
    if not DRY_RUN and shutil.which("claude") is None:
        print(
            "warning: 'claude' not found; skipping Claude payload validation (pass --no-validate to silence).",
            file=sys.stderr,
        )
        return
    print("==> Validating Claude Code payload ...")
    run_cmd(["claude", "plugin", "validate", str(claude_payload_dir())])


def command_output(args: list[str]) -> tuple[int, str]:
    completed = run_known_command(args, capture_output=True, check=False)
    return completed.returncode, completed.stdout


def claude_marketplace_root() -> tuple[int, str]:
    rc, listing = command_output(["claude", "plugin", "marketplace", "list"])
    if rc != 0:
        return 1, ""

    found = False
    for line in listing.splitlines():
        row = line.lstrip(" \t>❯").rstrip()
        if not found and row == MARKETPLACE:
            found = True
            continue
        if found and line.lstrip().startswith("Source: Directory ("):
            root = line.strip()
            root = root.removeprefix("Source: Directory (")
            root = root.removesuffix(")")
            return 0, root
        if found and line.lstrip().startswith("Source:"):
            return 2, ""
    return (2, "") if found else (0, "")


def ensure_claude_marketplace_is_local() -> None:
    if DRY_RUN:
        print(f"+ claude plugin marketplace list # verify {MARKETPLACE} points at {shlex.quote(str(REPO_ROOT))}")
        return

    rc, root = claude_marketplace_root()
    if rc == 2:
        die(
            f"Claude marketplace '{MARKETPLACE}' exists but is not a local Directory source. "
            f"Remove it (claude plugin marketplace remove '{MARKETPLACE}') before refreshing."
        )
    if rc != 0:
        die("failed to inspect Claude marketplace list")
    if root == str(REPO_ROOT):
        return
    if root:
        die(f"Claude marketplace '{MARKETPLACE}' points at '{root}', expected '{REPO_ROOT}'. Remove or update it explicitly before refreshing.")

    print(f"==> Adding Claude marketplace {MARKETPLACE} from {REPO_ROOT} ...")
    run_cmd(["claude", "plugin", "marketplace", "add", str(REPO_ROOT), "--scope", CLAUDE_SCOPE])


def refresh_claude_install() -> None:
    require_cmd("claude")
    ensure_claude_marketplace_is_local()

    print(f"==> Refreshing {plugin_selector()} in Claude Code ({CLAUDE_SCOPE} scope) ...")
    if DRY_RUN:
        print(f"+ claude plugin uninstall {shlex.quote(plugin_selector())} --scope {shlex.quote(CLAUDE_SCOPE)} -y")
    else:
        completed = subprocess.run(
            ["claude", "plugin", "uninstall", plugin_selector(), "--scope", CLAUDE_SCOPE, "-y"],
            text=True,
            capture_output=True,
            shell=False,
            check=False,
        )
        if completed.returncode != 0:
            output = completed.stdout + completed.stderr
            if "not installed" not in output and "not found" not in output:
                print(output, file=sys.stderr, end="" if output.endswith("\n") else "\n")
                die(f"failed to uninstall {plugin_selector()} from Claude Code")
    run_cmd(["claude", "plugin", "install", plugin_selector(), "--scope", CLAUDE_SCOPE])
    print("    Restart Claude Code or run /reload-plugins in an existing session.")


def codex_marketplace_root() -> tuple[int, str]:
    rc, listing = command_output(["codex", "plugin", "marketplace", "list"])
    if rc != 0:
        return 1, ""
    for line in listing.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0] == MARKETPLACE:
            return 0, parts[1]
    return 0, ""


def ensure_codex_marketplace_is_local() -> None:
    if DRY_RUN:
        print(f"+ codex plugin marketplace list # verify {MARKETPLACE} points at {shlex.quote(str(REPO_ROOT))}")
        return

    rc, root = codex_marketplace_root()
    if rc != 0:
        die("failed to inspect Codex marketplace list")
    if root == str(REPO_ROOT):
        return
    if root:
        die(f"Codex marketplace '{MARKETPLACE}' points at '{root}', expected '{REPO_ROOT}'. Remove or update it explicitly before refreshing.")

    print(f"==> Adding Codex marketplace {MARKETPLACE} from {REPO_ROOT} ...")
    run_cmd(["codex", "plugin", "marketplace", "add", str(REPO_ROOT)])


def refresh_codex_install() -> None:
    require_cmd("codex")
    ensure_codex_marketplace_is_local()

    print(f"==> Refreshing {plugin_selector()} in Codex ...")
    if DRY_RUN:
        print(f"+ codex plugin remove {shlex.quote(plugin_selector())}")
    else:
        completed = subprocess.run(
            ["codex", "plugin", "remove", plugin_selector()],
            text=True,
            capture_output=True,
            shell=False,
            check=False,
        )
        if completed.returncode != 0:
            output = completed.stdout + completed.stderr
            if "not installed" not in output and "not found" not in output:
                print(output, file=sys.stderr, end="" if output.endswith("\n") else "\n")
                die(f"failed to remove {plugin_selector()} from Codex")
    run_cmd(["codex", "plugin", "add", plugin_selector()])
    print("    Start a new Codex thread to pick up refreshed plugin skills and tools.")


def launch_claude_with_local_payload() -> None:
    require_cmd("claude")
    print("==> Launching Claude Code with local payload override ...")
    run_cmd(["claude", "--plugin-dir", str(claude_payload_dir())])


def print_guidance() -> None:
    if not RUN_CLAUDE_LAUNCH:
        print()
        print("Claude Code local-development command:")
        print(f"  {claude_dev_command()}")
    if not RUN_CLAUDE_INSTALL:
        print("Skipped Claude installed-cache refresh (--no-claude-install).")
    if not RUN_CODEX:
        print("Skipped Codex installed-cache refresh (--no-codex).")


def main(argv: list[str]) -> int:
    try:
        parse_args(argv)
        validate_layout()
        if RUN_BUILD:
            build_payloads()
        if RUN_VALIDATE:
            validate_claude_payload()
        if RUN_CODEX:
            refresh_codex_install()
        if RUN_CLAUDE_INSTALL:
            refresh_claude_install()
        if RUN_CLAUDE_LAUNCH:
            launch_claude_with_local_payload()
        print_guidance()
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(file=sys.stderr)
        print(USAGE, file=sys.stderr, end="")
        return 2
    except FatalError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        return exc.returncode or 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
