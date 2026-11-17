#!/usr/bin/env python3
"""Dispatch the changed-path policy and repository checks for PR Checks."""

from __future__ import annotations

import argparse
import subprocess
import os
import sys
from collections.abc import Sequence
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
import changed_files as _changed_files  # noqa: E402
import ci_selection  # noqa: E402
from ci_environment import build_environment  # noqa: E402
from process_status import shell_compatible_status  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


class PluginMatrixError(RuntimeError):
    """Raised when the plugin matrix cannot be emitted."""


def append_plugin_matrix(output_path: Path, changed_files: Sequence[str] | None = None) -> str:
    fields = ci_selection.select_checks(changed_files)
    try:
        with output_path.open("a", encoding="utf-8", newline="\n") as output:
            output.writelines(f"{name}={value}\n" for name, value in fields.items())
    except OSError as error:
        raise PluginMatrixError(f"unable to append GITHUB_OUTPUT: {error}") from error
    return fields["plugins"]


def run_repository_checks() -> int:
    """Run the suite's marked checks with the same clean Git identity as CI."""
    environment = build_environment(os.environ)
    for path in ci_selection.repository_checks():
        print(f"Repository check: {path}", flush=True)
        completed = subprocess.run(
            [sys.executable, path], cwd=REPO_ROOT, env=environment, check=False, shell=False,
        )
        if completed.returncode:
            return shell_compatible_status(completed.returncode)
    request = (REPO_ROOT / ci_selection.REPOSITORY_GATE_REQUEST).read_bytes()
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"], input=request,
        cwd=REPO_ROOT, env=environment, check=False, shell=False,
    )
    return shell_compatible_status(completed.returncode)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-checks", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.repository_checks:
            return run_repository_checks()
        output_value = os.environ.get("GITHUB_OUTPUT", "")
        if not output_value:
            raise PluginMatrixError("GITHUB_OUTPUT is not set")
        try:
            changed_files = _changed_files.changed_files_for_base(
                os.environ.get("BASE_REF", ""), repo_root=REPO_ROOT, error=PluginMatrixError,
                include_rename_sources=True,
            )
        except (PluginMatrixError, UnicodeError) as error:
            print(f"::warning::{error}; selecting the full suite and Go")
            changed_files = None
        encoded = append_plugin_matrix(Path(output_value), changed_files)
    except (PluginMatrixError, OSError, ValueError) as error:
        print(f"::error::{error}", file=sys.stderr)
        return 1
    print(f"Python-gated plugin matrix: {encoded}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
