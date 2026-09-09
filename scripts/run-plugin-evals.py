#!/usr/bin/env python3
"""Run `claude plugin eval` from the repository root with explicit fan-out.

Why this wrapper exists
-----------------------
`claude plugin eval` multiplies work in two directions that are easy to miss:

* ``--runs`` defaults to ``case.runs ?? 3`` -- three agent sessions per case.
* ``--ablation`` defaults to ``with-without`` -- a second, no-plugin baseline
  arm, doubling that again.

So the default invocation is **six agent sessions per eval case**, and each one
pays its own full context boot.

The second failure mode is the working directory. Claude Code resolves plugin
and MCP configuration from the launch directory, so an eval started from
``$HOME`` inherits the home default rather than this repository's loadout. The
results are then neither reproducible nor attributable to the project.

This wrapper fixes both: it refuses to run outside the repository, chdir's to
the repo root, and makes the fan-out an explicit choice.

Usage
-----
    scripts/run-plugin-evals.py speckit-pro                 # iterate: 1 run, no baseline
    scripts/run-plugin-evals.py speckit-pro --full          # gate: full 3 x 2 fan-out
    scripts/run-plugin-evals.py speckit-pro --case 'status*'
    scripts/run-plugin-evals.py speckit-pro -- --tag smoke  # pass through to the CLI

Anything after ``--`` is forwarded to ``claude plugin eval`` unchanged.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Iterating locally: one run, no baseline arm. 1/6th the sessions of the
# default.
ITERATE_ARGS = ["--runs", "1", "--ablation", "none"]

DEFAULT_ITERATE_BUDGET_USD = "5"
DEFAULT_FULL_BUDGET_USD = "25"


def repo_root() -> Path:
    """Return the git top level, or exit if we are not inside a checkout."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        sys.exit("run-plugin-evals: git is not on PATH.")
    if out.returncode != 0 or not out.stdout.strip():
        sys.exit(
            "run-plugin-evals: refusing to run outside a git checkout "
            f"(cwd={Path.cwd()}).\n"
            "Evals must run from the repository root so they inherit this "
            "project's plugin configuration, not your home default."
        )
    return Path(out.stdout.strip())


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run-plugin-evals.py",
        description="Run plugin evals from the repo root with explicit fan-out.",
        epilog="Arguments after `--` are forwarded to `claude plugin eval`.",
    )
    p.add_argument(
        "target",
        help="Plugin name, `plugin@marketplace` id, or a path to a plugin.",
    )
    p.add_argument(
        "--full",
        action="store_true",
        help="Release-gate mode: keep the CLI defaults (3 runs x 2 ablation "
             "arms = 6 sessions per case) instead of the lean iterate profile.",
    )
    p.add_argument(
        "--case",
        help="Filter cases by name glob, forwarded to `--case`.",
    )
    p.add_argument(
        "--max-cost-usd",
        help="Hard cost ceiling. Defaults to "
             f"{DEFAULT_ITERATE_BUDGET_USD} when iterating and "
             f"{DEFAULT_FULL_BUDGET_USD} with --full.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command that would run, then exit.",
    )
    return p


def main(argv: list[str]) -> int:
    if "--" in argv:
        split = argv.index("--")
        argv, passthrough = argv[:split], argv[split + 1:]
    else:
        passthrough = []

    args = build_parser().parse_args(argv)

    if shutil.which("claude") is None:
        sys.exit("run-plugin-evals: `claude` is not on PATH.")

    root = repo_root()
    os.chdir(root)

    budget = args.max_cost_usd or (
        DEFAULT_FULL_BUDGET_USD if args.full else DEFAULT_ITERATE_BUDGET_USD
    )

    cmd = ["claude", "plugin", "eval", args.target, "--max-cost-usd", budget]
    if not args.full:
        cmd.extend(ITERATE_ARGS)
    if args.case:
        cmd.extend(["--case", args.case])
    cmd.extend(passthrough)

    profile = "full (3 runs x 2 arms)" if args.full else "iterate (1 run, no baseline)"
    print(f"run-plugin-evals: root    {root}")
    print(f"run-plugin-evals: profile {profile}")
    print(f"run-plugin-evals: budget  ${budget}")
    print("run-plugin-evals: $ " + " ".join(cmd))

    if args.dry_run:
        return 0
    return subprocess.run(cmd, cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
