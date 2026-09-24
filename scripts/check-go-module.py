#!/usr/bin/env python3
"""Run the Go module checks for typesafe-jev in the PR Checks workflow.

Go is the plugin-owned toolchain for typesafe-jev/. This wrapper is the
repository side of that boundary: it only calls the Go tools, with argv lists
and no shell.

Modes:

  detect  Append run_go=true or run_go=false to GITHUB_OUTPUT, from the files
          changed against origin/$BASE_REF.
  check   Verify module checksums, check formatting, vet, test, test with the
          race detector, and cross-compile every release target.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = "typesafe-jev"
# A change to the module, to this wrapper, or to the workflow that runs it can
# change the Go result, so each one runs the Go job.
TRIGGER_PATHS = frozenset({"scripts/check-go-module.py", ".github/workflows/pr-checks.yml"})
RELEASE_TARGETS = (
    ("darwin", "amd64"),
    ("darwin", "arm64"),
    ("linux", "amd64"),
    ("linux", "arm64"),
)


class GoModuleCheckError(RuntimeError):
    """Raised when a Go module check cannot run or does not pass."""


def go_module_changed(changed_files: Iterable[str]) -> bool:
    for file_path in changed_files:
        if file_path.startswith(f"{MODULE_DIR}/") or file_path in TRIGGER_PATHS:
            return True
    return False


def changed_files_for_base(base_ref: str, *, repo_root: Path = REPO_ROOT) -> tuple[str, ...]:
    if not base_ref:
        raise GoModuleCheckError("BASE_REF is not set")
    try:
        completed = subprocess.run(
            ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=True,
            shell=False,
        )
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or "").strip()
        suffix = f": {detail}" if detail else ""
        raise GoModuleCheckError(
            f"git changed-file detection failed with exit code {error.returncode}{suffix}"
        ) from error
    except OSError as error:
        raise GoModuleCheckError(f"unable to run git changed-file detection: {error}") from error
    return tuple(completed.stdout.splitlines())


def append_github_output(output_path: Path, fields: Mapping[str, str]) -> None:
    try:
        with output_path.open("a", encoding="utf-8", newline="\n") as output:
            for key, value in fields.items():
                output.write(f"{key}={value}\n")
    except OSError as error:
        raise GoModuleCheckError(f"unable to append GITHUB_OUTPUT: {error}") from error


def detect() -> None:
    run_go = go_module_changed(changed_files_for_base(os.environ.get("BASE_REF", "")))
    output_value = os.environ.get("GITHUB_OUTPUT", "")
    if not output_value:
        raise GoModuleCheckError("GITHUB_OUTPUT is not set")
    print(f"Go module checks needed: {'true' if run_go else 'false'}")
    append_github_output(Path(output_value), {"run_go": "true" if run_go else "false"})


def finish(argv: Sequence[str], completed: subprocess.CompletedProcess[str]) -> str:
    """Echo one Go tool's output and return its stdout, or raise on failure."""
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.stderr:
        print(completed.stderr, end="" if completed.stderr.endswith("\n") else "\n", file=sys.stderr)
    if completed.returncode != 0:
        raise GoModuleCheckError(f"{' '.join(argv)} failed with exit code {completed.returncode}")
    return completed.stdout


def run_go(*args: str, env: Mapping[str, str] | None = None) -> str:
    """Run `go` with args in the module directory and return its stdout."""
    argv = ["go"]
    argv.extend(args)
    print(f"$ {' '.join(argv)}", flush=True)
    try:
        completed = subprocess.run(
            argv,
            cwd=REPO_ROOT / MODULE_DIR,
            env=None if env is None else {**os.environ, **env},
            text=True,
            capture_output=True,
            check=False,
            shell=False,
        )
    except OSError as error:
        raise GoModuleCheckError(f"unable to run go: {error}") from error
    return finish(argv, completed)


def run_gofmt(*args: str) -> str:
    """Run `gofmt` with args in the module directory and return its stdout."""
    argv = ["gofmt"]
    argv.extend(args)
    print(f"$ {' '.join(argv)}", flush=True)
    try:
        completed = subprocess.run(
            argv,
            cwd=REPO_ROOT / MODULE_DIR,
            text=True,
            capture_output=True,
            check=False,
            shell=False,
        )
    except OSError as error:
        raise GoModuleCheckError(f"unable to run gofmt: {error}") from error
    return finish(argv, completed)


def check() -> None:
    run_go("mod", "verify")
    unformatted = run_gofmt("-l", ".").split()
    if unformatted:
        raise GoModuleCheckError(f"gofmt would reformat: {', '.join(unformatted)}")
    run_go("vet", "./...")
    run_go("test", "-count=1", "./...")
    # Separate from the static builds below, which set CGO_ENABLED=0. The race
    # detector needs cgo.
    run_go("test", "-race", "-count=1", "./...")
    with tempfile.TemporaryDirectory(prefix="typesafe-jev-build-") as build_dir:
        for goos, goarch in RELEASE_TARGETS:
            output = str(Path(build_dir) / f"evaluate-{goos}-{goarch}")
            run_go(
                "build",
                "-trimpath",
                "-o",
                output,
                "./cmd/evaluate",
                env={"CGO_ENABLED": "0", "GOOS": goos, "GOARCH": goarch},
            )


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    modes = {"detect": detect, "check": check}
    try:
        if len(args) != 1 or args[0] not in modes:
            raise GoModuleCheckError("usage: check-go-module.py detect|check")
        modes[args[0]]()
    except GoModuleCheckError as error:
        print(f"::error::Go module check failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
